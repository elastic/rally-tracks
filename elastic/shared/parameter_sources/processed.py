# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import copy
import time
from typing import Tuple
import logging
import math
import random
from datetime import datetime, timezone

from shared.parameter_sources import DEFAULT_END_DATE, DEFAULT_START_DATE
from shared.utils.track import mandatory
from esrally.track import exceptions
from esrally.track.params import IndexIdConflict
from esrally.utils import io

from shared.ts_generators import get_ts_generator
from shared.utils.corpus import bounds, convert_to_gib
from shared.utils.file import BulkFileReader, WrappingSlice, CorpusReader
from shared.utils.time import parse_date_time


class MagicNumbers:
    # The following magic markers are used as fixed positions in the json docstring to speed up bulk indexing
    # (see data_generation.py._append_doc_markers() for more details)
    #
    # Example doc: (total un-truncated length until "markers" is 1969 bytes
    # {... various fields ..., "message": "1:M _RALLYTS014<%d %b %H:%M:%S>.332 - Client closed connection",... various fields ..., "rally": {"message_size": 50, "doc_size": 1796, "markers": "00000001a300000004f00000000508000000079b000000079d"}}

    # each generated doc has a "markers": "" object at the end
    # contains five 10digit hex numbers indicating corresponding positions of importance in the doc string
    MARKER_IDX = -67  # index of `,` in `... , "markers": "..."}}`
    RALLYTS_BEGIN_IDX = -53  # index of _ in `_RALLYTS...`
    TS_BEGIN_IDX = -43  # index of opening `"` of @timestamp value
    TS_END_IDX = -33  # closing `"` in ^^^
    MSGLEN_BEGIN_IDX = -23  # where the value of `"rally": {"message_size": ` begins
    MSGLEN_END_IDX = -13  # where ^^^ ends

    # most seed data have a `_RALLYTSNNN<ts format string>` placeholder in the message field
    # containing the timestamp format
    # vars below contain positions/length from the placeholder start
    RALLYTS_LEN = 8  # len("_RALLYTS")
    RALLYTSDATA_LEN = 3  # len(NNN) (always 3 digits)
    RALLYTSDATA_LEN_END = 11  # position of character before <
    RALLYTS_FORMAT_BEGIN = 12  # position of first character after <


class ProcessedCorpusParamSource:
    def __init__(self, track, params, **kwargs):
        self.logger = logging.getLogger(__name__)
        self._orig_args = [track, params, kwargs]
        # allows to be specified for testing only
        self.track = track
        self._complete = False
        self.infinite = False
        self._params = params
        self.kwargs = kwargs
        self._track_id = track.selected_challenge_or_default.parameters["track-id"]
        self._random_seed = track.selected_challenge_or_default.parameters.get(
            "random-seed", None
        )
        self.logger.info(f"Using track id {self._track_id}")
        raw_volume_per_day = mandatory(
            track.selected_challenge_or_default.parameters,
            "raw-data-volume-per-day",
            "bulk",
        )
        self._volume_per_day_gb = convert_to_gib(raw_volume_per_day)
        self.start_time = int(time.perf_counter())
        self._profile = params.get("profile", "fixed_interval")
        now = datetime.utcnow().replace(tzinfo=timezone.utc)

        def utc_now():
            return now

        if params.get("init-load", False):
            # this is an undocumented parameter that causes bulk-start-date and bulk-end-date to be used for pre loading
            # datasets in cases where multiple challenges cannot be run
            self._start_date = parse_date_time(
                track.selected_challenge_or_default.parameters.get(
                    "bulk-start-date", DEFAULT_START_DATE
                ),
                utcnow=utc_now,
            )
            self._end_date = parse_date_time(
                track.selected_challenge_or_default.parameters.get(
                    "bulk-end-date", DEFAULT_END_DATE
                ),
                utcnow=utc_now,
            )
        else:
            self._start_date = parse_date_time(
                track.selected_challenge_or_default.parameters.get(
                    "start-date", DEFAULT_START_DATE
                ),
                utcnow=utc_now,
            )
            self._end_date = parse_date_time(
                track.selected_challenge_or_default.parameters.get(
                    "end-date", DEFAULT_END_DATE
                ),
                utcnow=utc_now,
            )

        self.logger.info(
            "Using date range [%s] to [%s] for " "indexing",
            self._start_date.isoformat(),
            self._end_date.isoformat(),
        )

        if self._start_date > self._end_date:
            raise exceptions.TrackConfigError(
                f'"start-date" cannot be greater than "end-date" for operation '
                f"\"{self._params.get('operation-type')}\""
            )
        self._number_of_days = (
            self._end_date - self._start_date
        ).total_seconds() / 86400

        self._time_format = params.get("time-format", "milliseconds")
        self._processor = self._json_processor
        # we have meta in our bulk and don't need these for solution tracks and datastreams
        self.id_conflicts = IndexIdConflict.NoConflicts
        self.conflict_probability = None
        self.on_conflict = None
        self.recency = None
        # defer to bulk as blended
        self.pipeline = None
        try:
            self.bulk_size = int(mandatory(params, "bulk-size", "bulk"))
            if self.bulk_size <= 0:
                raise exceptions.InvalidSyntax(
                    f'"bulk-size" must be positive but was {self.bulk_size}'
                )
            # each doc needs consists of meta and doc
            self.lines_per_bulk = self.bulk_size * 2
        except KeyError:
            raise exceptions.InvalidSyntax('Mandatory parameter "bulk-size" is missing')
        except ValueError:
            raise exceptions.InvalidSyntax('"bulk-size" must be numeric')
        self.corpus = next(
            (c for c in track.corpora if c.meta_data.get("generated", False)), None
        )
        self._reset_timestamps()
        # TODO: Validate this exists and has files
        self.current_docs = 0
        # Set to 1 to avoid division by zero if percent_completed is called before this parameter has
        # been initialized to its actual value (i.e. before the first call to #params()),
        self.docs_per_client = 1

    def _reset_timestamps(self):
        self.min_timestamp = datetime.max.replace(tzinfo=timezone.utc)
        self.max_timestamp = datetime.min.replace(tzinfo=timezone.utc)
        self.event_time_span = 0

    def partition(self, partition_index, total_partitions):
        self.logger.info("[%s]/[%s]", partition_index, total_partitions)
        seed = partition_index * self._random_seed if self._random_seed else None
        random.seed(seed)
        new_params = copy.deepcopy(self._params)
        new_params["client_index"] = partition_index
        new_params["client_count"] = total_partitions
        return ProcessedCorpusParamSource(
            self._orig_args[0], new_params, **self._orig_args[2]
        )

    def _json_processor(self, doc: bytes, line_num: int, _: str) -> Tuple[str, int]:
        doc = doc.decode("utf-8").strip()
        if line_num % 2 == 0:
            return doc, 0
        # adds the timestamp to docs not metadata lines which will be in generated files
        timestamp = self._ts_generator.next_timestamp()
        # we assume date order - maybe speed this up for a boolean check on first request?
        if timestamp < self.min_timestamp:
            self.min_timestamp = timestamp
        self.max_timestamp = timestamp

        # see ProcessedCorpusParamSource for more details
        rallyts_start_pos = int(
            doc[MagicNumbers.RALLYTS_BEGIN_IDX : MagicNumbers.TS_BEGIN_IDX], 16
        )
        msglen_value_start_pos = int(
            doc[MagicNumbers.MSGLEN_BEGIN_IDX : MagicNumbers.MSGLEN_END_IDX], 16
        )
        msglen_value_end_pos = int(
            doc[MagicNumbers.MSGLEN_END_IDX : MagicNumbers.MSGLEN_END_IDX + 10], 16
        )

        msgsize = int(doc[msglen_value_start_pos:msglen_value_end_pos], 10)

        if rallyts_start_pos != -1:
            # doc["message"] contains _RALLYTS with timestamp format specification (most of integrations)

            rallyts_len = int(doc[rallyts_start_pos+MagicNumbers.RALLYTS_LEN: rallyts_start_pos + MagicNumbers.RALLYTSDATA_LEN_END], 10)

            ts_format = doc[rallyts_start_pos + MagicNumbers.RALLYTS_FORMAT_BEGIN: rallyts_start_pos + MagicNumbers.RALLYTS_FORMAT_BEGIN + rallyts_len]
            formatted_ts = time.strftime(ts_format, timestamp.timetuple())

            # replace _RALLYTSNNN<...> with generated timestamp in the right format
            # and omit the "markers" key
            doc = (
                f"{doc[:rallyts_start_pos]}"
                f"{formatted_ts}"
                f"{doc[rallyts_start_pos + MagicNumbers.RALLYTS_FORMAT_BEGIN + rallyts_len + 1: MagicNumbers.MARKER_IDX]}"
                f"}}}}"
            )
        else:
            # no timestamp in message field e.g. application-logs, redis-slowlog-log
            # directly copy timestamp in a format compatible with the `date` ES field (`strict_date_optional_time`)

            ts_value_start_pos = int(
                doc[MagicNumbers.TS_BEGIN_IDX : MagicNumbers.TS_END_IDX], 16
            )
            ts_value_end_pos = int(
                doc[MagicNumbers.TS_END_IDX : MagicNumbers.MSGLEN_BEGIN_IDX], 16
            )

            formatted_ts = "%04d-%02d-%02dT%02d:%02d:%02d" % (
                timestamp.year,
                timestamp.month,
                timestamp.day,
                timestamp.hour,
                timestamp.minute,
                timestamp.second,
            )

            # prevent Elasticsearch achieving unrealistically high compression levels
            # by varying the millisecond suffix in the timestamp with minimal cpu overhead
            LARGEINT = 123132434 + line_num

            # replace @timestamp value with generated timestamp
            # and omit the "markers" key
            doc = (
                f"{doc[:ts_value_start_pos]}"
                f"""{formatted_ts}.{LARGEINT % 1000}Z"""
                f"{doc[ts_value_end_pos: MagicNumbers.MARKER_IDX]}"
                f"}}}}"
            )

        return doc, msgsize

    def create_bulk_corpus_reader(
        self, corpus, bulk_size, processor, num_clients, client_index
    ):
        readers = []
        for docs in corpus.documents:
            # we want even offsets or docs and meta will be separated
            self.logger.debug(
                "Task-relative clients at index [%d-%d] using [%s] which has [%d] documents from corpus "
                "name [%s]",
                client_index,
                num_clients,
                docs.document_file,
                docs.number_of_documents,
                corpus.name,
            )
            offset, num_docs = bounds(
                docs.number_of_documents, client_index, num_clients, ensure_even=True
            )
            if num_docs > 0:
                self.logger.debug(
                    "Task-relative clients at index [%d-%d] will read [%d] docs starting from line offset "
                    "[%d] for [%s] from corpus [%s] at file[%s].",
                    client_index,
                    num_clients,
                    num_docs,
                    offset,
                    docs.target_data_stream,
                    corpus.name,
                    docs.document_file,
                )
                # multiple offset and num docs by 2 to account for meta lines
                source = WrappingSlice(io.MmapSource, offset * 2, num_docs * 2)
                readers.append(
                    BulkFileReader(docs.document_file, source, processor, corpus.name)
                )
            else:
                self.logger.info(
                    "Task-relative clients at index [%d-%d] skip [%s] (no documents to read).",
                    client_index,
                    num_clients,
                    corpus.name,
                )
        return CorpusReader(readers, bulk_size)

    def _doc_generator(self, num_clients, client_index):
        report_size = self.bulk_size * 10
        # if each client needs more than the total number of docs in corpus we might as well have each client loop over
        # all of them
        if self.docs_per_client > self.total_corpus_docs:
            self.corpus_reader = self.create_bulk_corpus_reader(
                self.corpus,
                self.lines_per_bulk,
                self._processor,
                num_clients=1,
                client_index=0,
            )
        else:
            # each client gets a section of the files
            self.corpus_reader = self.create_bulk_corpus_reader(
                self.corpus,
                self.lines_per_bulk,
                self._processor,
                num_clients,
                client_index,
            )
        params = self._params.copy()
        with self.corpus_reader:
            while not self._complete:
                num_docs, lines, raw_size_in_bytes = next(self.corpus_reader)
                if self.current_docs + num_docs >= self.docs_per_client:
                    self._complete = True
                    self.logger.info("Completed with [%s] docs", self.docs_per_client)
                    # we deliberately don't trim the last batch to get the exact number of documents. This would break
                    # encapsulation and this shouldn't be an issue on larger datasets
                elif self.current_docs > 0 and self.current_docs % report_size == 0:
                    self.logger.debug("[%s] docs indexed", self.current_docs)
                self.current_docs += num_docs
                params["body"] = lines
                params["unit"] = "docs"
                params["action-metadata-present"] = True
                params["bulk-size"] = num_docs
                self.event_time_span = (
                    self.max_timestamp - self.min_timestamp
                ).total_seconds()
                relative_time = int(time.perf_counter()) - self.start_time
                params["param-source-stats"] = {
                    "client": client_index,
                    "raw-size-bytes": raw_size_in_bytes,
                    "event-time-span": self.event_time_span,
                    "relative-time": relative_time,
                    "index-lag": self.event_time_span - relative_time,
                    "min-timestamp": self.min_timestamp.isoformat(
                        sep="T", timespec=self._time_format
                    ),
                    "max-timestamp": self.max_timestamp.isoformat(
                        sep="T", timespec=self._time_format
                    ),
                }
                yield params

    def _init_internal_params(self):
        self._client_count = self._params["client_count"]
        self._client_index = self._params["client_index"]
        self.total_corpus_docs = 0
        self.total_corpus_bytes = 0
        for docs in self.corpus.documents:
            self.total_corpus_docs += docs.number_of_documents
            self.total_corpus_bytes += docs.message_size
        self.total_docs_per_day = math.ceil(
            self.total_corpus_docs
            * ((self._volume_per_day_gb * 1024 * 1024 * 1024) / self.total_corpus_bytes)
        )
        self.total_docs = self.total_docs_per_day * self._number_of_days
        if self._client_index == 0:
            self.logger.info(f"Total Docs: [{self.total_docs}]")
            self.logger.info(f"Docs per Day: [{self.total_docs_per_day}]")
        _, self.docs_per_client = bounds(
            self.total_docs, self._client_index, self._client_count
        )
        self._ts_generator = get_ts_generator(
            self._profile, self.total_docs_per_day, self._start_date, self._client_count
        )
        self.logger.info(
            f"Docs for client [{self._client_count}]: [{self.docs_per_client}]"
        )
        self.logger.info(
            f"Initializing client [{self._client_index}/{self._client_count}]"
        )
        self.doc_generator = self._doc_generator(self._client_count, self._client_index)

    @property
    def percent_completed(self):
        if not self._complete:
            return self.current_docs / self.docs_per_client
        return 1.0

    def params(self):
        if self.current_docs == 0:
            self._init_internal_params()
        return next(self.doc_generator)

    def set_bulk_size(self, bulk_size):
        # each doc consists of a doc + meta
        self.corpus_reader.set_bulk_size(bulk_size * 2)

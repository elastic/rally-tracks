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

import glob
import json
import logging
import os
import random

from esrally import exceptions
from esrally.track import DocumentCorpus, Documents
from esrally.track.loader import DocumentSetPreparator
from esrally.utils import io

from shared.parameter_sources import DEFAULT_END_DATE, DEFAULT_START_DATE, utc_now
from shared.utils.corpus import (
    calculate_corpus_counts,
    calculate_integration_ratios,
    bounds,
    convert_to_gib,
)
from shared.utils.file import FileMetadata
from shared.utils.file import JsonFileReader, WrappingSlice, CorpusReader, CorporaReader
from shared.utils.time import parse_date_time
from shared.utils.track import mandatory


class LazyMetadataDocuments(Documents):
    def __init__(self, document_file):
        super().__init__(
            source_format=Documents.SOURCE_FORMAT_BULK,
            document_file=document_file,
            includes_action_and_meta_data=True,
        )

    @property
    def uncompressed_size_in_bytes(self):
        try:
            return os.path.getsize(self.document_file)
        # called before data have been generated (e.g. when listing tracks)
        except FileNotFoundError:
            return 0

    @property
    def metadata(self):
        return FileMetadata.read(self.document_file[: -len(".json")])

    @property
    def number_of_documents(self):
        try:
            return self.metadata[0]
        # called before data have been generated (e.g. when listing tracks)
        except FileNotFoundError:
            return 0

    @number_of_documents.setter
    def number_of_documents(self, value):
        # ignore any attempts to change the number of documents (e.g. via test mode)
        pass

    @property
    def message_size(self):
        try:
            return self.metadata[1]
        except FileNotFoundError:
            return 0


class DataGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # just declare here, will be injected later
        self.downloader = None
        self.decompressor = None

    def on_after_load_track(self, track):
        if not track.selected_challenge_or_default.parameters.get(
            "generate-data", True
        ):
            return
        # inject a generated corpus
        track_id = track.selected_challenge_or_default.parameters["track-id"]
        client_count = track.selected_challenge_or_default.parameters.get(
            "data-generation-clients", 2
        )
        documents = []
        for client_id in range(client_count):
            # only use a relative path; the absolute path will be set by Rally on the target machine
            documents.append(
                LazyMetadataDocuments(
                    document_file=os.path.join(
                        "generated", track_id, f"{client_id}.json"
                    )
                )
            )

        # keep this corpus, as well as other corpora below the track directory by name it like the track
        generated_corpus = DocumentCorpus(
            name=track.name, documents=documents, meta_data={"generated": True}
        )
        track.corpora.append(generated_corpus)

    def on_prepare_track(self, track, data_root_dir):
        if not track.selected_challenge_or_default.parameters.get(
            "generate-data", True
        ):
            return []
        track_data_root = os.path.join(data_root_dir, track.name)
        for corpus in track.corpora:
            if not corpus.meta_data.get("generated", False):
                data_root = os.path.join(track_data_root, corpus.name)
                self.logger.info(
                    "Resolved data root directory for document corpus [%s] in track [%s] to [%s].",
                    corpus.name,
                    track.name,
                    data_root,
                )
                # only set for real benchmarks, not in unit tests
                if self.downloader and self.decompressor:
                    prep = DocumentSetPreparator(
                        track.name, self.downloader, self.decompressor
                    )

                    for document_set in corpus.documents:
                        prep.prepare_document_set(document_set, data_root)

        # data is now available locally, proceed with generating data
        client_count = track.selected_challenge_or_default.parameters.get(
            "data-generation-clients", 2
        )
        track_id = track.selected_challenge_or_default.parameters["track-id"]
        track.selected_challenge_or_default.parameters["output-folder"] = os.path.join(
            track_data_root, "generated", track_id
        )
        retval = []
        for client_id in range(client_count):
            generator_params = {
                "track": track,
                "track_data_root": track_data_root,
                "client_index": client_id,
                "client_count": client_count,
            }
            retval.append((generate, generator_params))
        return retval


class CorpusGenerator:
    def __init__(self, track, track_data_root, client_index="*", client_count=None):
        self.logger = logging.getLogger(__name__)
        self.include_doc_size_with_metadata = False
        self.corpora = []
        self.track = track
        self._random_seed = track.selected_challenge_or_default.parameters.get(
            "random-seed", None
        )
        self.track_data_root = track_data_root
        # check if output folder exists and contains files. If it does, we complete early unless force=True
        self.output_folder = track.selected_challenge_or_default.parameters[
            "output-folder"
        ]
        self.logger.info("Using output folder [%s]", self.output_folder)
        self.complete = False
        if not track.selected_challenge_or_default.parameters.get(
            "force-data-generation"
        ):
            file_pattern = f"{client_index}.json"
            if len(glob.glob(os.path.join(self.output_folder, file_pattern))) > 0:
                self.complete = True
                self.logger.info(
                    "Skipping data generation as files are present and force-data-generation is set to false."
                )

        self._client_index = client_index
        self._client_count = client_count

        self._integration_ratios = mandatory(
            track.selected_challenge_or_default.parameters,
            "integration-ratios",
            "generate-data",
        )
        self._exclude_properties = track.selected_challenge_or_default.parameters.get(
            "exclude-properties", {}
        )

        end_date = parse_date_time(
            track.selected_challenge_or_default.parameters.get(
                "end-date", DEFAULT_END_DATE
            ),
            utcnow=utc_now,
        )
        start_date = parse_date_time(
            track.selected_challenge_or_default.parameters.get(
                "start-date", DEFAULT_START_DATE
            ),
            utcnow=utc_now,
        )

        # bulk-end-date and bulk-start-date are undocumented and optional. If specified we generate data for the widest
        # date range possible as it will likely be re-used for incremental load.
        if bulk_end_date := track.selected_challenge_or_default.parameters.get(
            "bulk-end-date", None
        ):
            if (
                bulk_end_date := parse_date_time(bulk_end_date, utcnow=utc_now)
            ) > end_date:
                end_date = bulk_end_date

        if bulk_start_date := track.selected_challenge_or_default.parameters.get(
            "bulk-start-date", None
        ):
            if (
                bulk_start_date := parse_date_time(bulk_start_date, utcnow=utc_now)
            ) < start_date:
                start_date = bulk_start_date

        self.logger.info(
            "Using date range [%s] to [%s] for generation",
            start_date.isoformat(),
            end_date.isoformat(),
        )

        if start_date > end_date:
            raise exceptions.TrackConfigError(
                f'"start-date" cannot be greater than "end-date" for data generation.'
            )
        # number of days to run the test for - used to calculate the amount of data to generate
        number_of_days = (end_date - start_date).total_seconds() / 86400
        self._max_generation_size_gb = convert_to_gib(
            mandatory(
                track.selected_challenge_or_default.parameters,
                "max-generated-corpus-size",
                "generate-data",
            )
        )
        raw_volume_per_day = mandatory(
            track.selected_challenge_or_default.parameters,
            "raw-data-volume-per-day",
            "generate-data",
        )
        self._data_generation_gb = min(
            convert_to_gib(raw_volume_per_day) * number_of_days,
            self._max_generation_size_gb,
        )
        self.logger.info("[%s]GB of raw data to be generated", self._data_generation_gb)
        self._processor = self._json_processor

        # mainly for unit testing but can be modified and might be worth making this a factor of num clients later
        self._offset_increment = track.selected_challenge_or_default.parameters.get(
            "offset-increment", 50000
        )
        self._batch_size = mandatory(
            track.selected_challenge_or_default.parameters,
            "generator-batch-size",
            "generate-data",
        )
        # batch size cannot be greater than the offset increment or we will not generate offsets
        if self._batch_size > self._offset_increment:
            raise exceptions.RallyAssertionError(
                f"generator-batch-size [{self._batch_size}] cannot be greater than offset-increment "
                f"[{self._offset_increment}]"
            )
        ratio_total = 0
        # number of lines to sample from each corpus to identify the raw->json factor each corpus.
        # Principally for testing.
        self._sample_size = track.selected_challenge_or_default.parameters.get(
            "sample-size", 10000
        )
        for integration_name, integration in self._integration_ratios.items():
            for corpus_name, ratio in integration["corpora"].items():
                corpus = next((c for c in track.corpora if c.name == corpus_name), None)
                self.corpora.append(corpus)
                if not corpus:
                    raise exceptions.RallyAssertionError(
                        f"Corpus [{corpus_name}] is defined for data generation in integration [{integration_name}] "
                        f"but is not present in track"
                    )
                ratio_total += ratio

        if round(ratio_total, 3) != 1.0:
            raise exceptions.RallyAssertionError(
                f"Corpora ratios must total 1.0 - total is [{ratio_total}]"
            )

    def _json_processor(self, doc_bytes, _, corpus_name):
        # add any additional doc work here
        doc = json.loads(doc_bytes.decode("utf-8"))
        message_size = int(doc.pop("msglen", 0))
        remove_fields = self._exclude_properties.get(corpus_name, [])
        if len(remove_fields) > 0:
            for field in remove_fields:
                if field in doc:
                    del doc[field]
            # doc size after field removal! careful with whitespace
        doc_size = len(json.dumps(doc, separators=(",", ":")).encode("utf-8"))
        doc["rally"] = {}
        # Note: we rely on insertion order here for later efficient parsing - as of python 3.7 this is preserved
        doc["rally"]["message_size"] = message_size
        doc["rally"]["doc_size"] = doc_size
        # the following is not used for enriched data stored on disk, only for _sample_corpus_stats()
        # size with the rally meta, assign the doc size and timestamp temporarily so its included
        # Note: the doc size is only an estimate. It will often be modified by ingest pipelines so in subject to change.
        if self.include_doc_size_with_metadata:
            doc["rally"]["doc_size_with_meta"] = doc_size
            doc["rally"]["doc_size_with_meta"] = len(
                json.dumps(doc, separators=(",", ":")).encode("utf-8")
            )

        self._append_doc_markers(doc)
        return doc, doc["rally"]["message_size"]

    @staticmethod
    def _append_doc_markers(doc):
        """
        Adds fixed length index markers, using the key "markers", at the end of the generated doc
        to make speed up bulk indexing and avoid expensive find() calls.

        Example:

        ... ,"rally": {"message_size": 165, "doc_size": 1960, "markers": "000000042300000000100000000028000000083f0000000842"}}

        `markers` is a 50byte string storing 5x10byte hexstrings, each representing the following positions
        in the serialized doc where, in the following order:

        1: `_RALLYTSNNN<... strf statement ...>` starts (10bytes)
        2, 3: the *value* for `@timestamp` starts and ends (10 + 10bytes)
        4, 5: the *value* for `"rally": {"message_size": ...` starts and ends (10 + 10bytes)

        `markers` is added as the last key in the `rally` object with order preserved since Python 3.7: therefore
        the index of `,` before "markers" in the serialized doc is always doc[-67:] (we serialize the generated docs
        using a single space after : and ,)

        The key `markers` is removed prior to ingestion.
        """

        # generated data, as stored on disk, uses the default separators i.e. ', ' and ': '
        raw_string = json.dumps(doc)

        _rallyts_token = "_RALLYTS"
        _rallyts_start_idx = raw_string.find(_rallyts_token)

        _ts_token = '@timestamp": "'
        _ts_start_idx = raw_string.find(_ts_token) + len(_ts_token)
        _ts_end_idx = _ts_start_idx + raw_string[_ts_start_idx:].find('"')

        _msgsize_token = '"rally": {"message_size": '
        _msgsize_start_idx = raw_string.find(_msgsize_token) + len(_msgsize_token)
        _msgsize_end_idx = _msgsize_start_idx + raw_string[_msgsize_start_idx:].find(
            ","
        )

        doc["rally"][
            "markers"
        ] = f"{_rallyts_start_idx:010x}{_ts_start_idx:010x}{_ts_end_idx:010x}{_msgsize_start_idx:010x}{_msgsize_end_idx:010x}"

    def create_corpus_reader(
        self, corpus, num_clients, client_index, bulk_size, processor
    ):
        readers = []
        for docs in corpus.documents:
            # Give each client a designated chunk of the file to use. Note: this will result in out of order delivery.
            # Maybe each client could consume each Nth line, where N = client num.
            # This will likely result in more seeking and less performance.
            offset, num_docs = bounds(
                docs.number_of_documents, client_index, num_clients
            )
            if num_docs > 0:
                self.logger.info(
                    "Generator [%d] will read [%d] docs starting from line offset [%d] for [%s] from corpus [%s].",
                    client_index,
                    num_docs,
                    offset,
                    docs.target_data_stream,
                    corpus.name,
                )
                source = WrappingSlice(io.MmapSource, offset, num_docs)
                readers.append(
                    JsonFileReader(
                        os.path.join(
                            self.track_data_root, corpus.name, docs.document_file
                        ),
                        source,
                        processor,
                        docs.target_data_stream,
                        corpus.name,
                    )
                )
            else:
                self.logger.info(
                    "Generator [%d] skips [%s] (no documents to read).",
                    client_index,
                    corpus.name,
                )
        return CorpusReader(readers, bulk_size)

    def _create_readers(self, num_clients, client_index):
        readers = {}
        for corpus in self.corpora:
            readers[corpus.name] = self.create_corpus_reader(
                corpus, num_clients, client_index, self._batch_size, self._processor
            )
        return readers

    def _reader_generator(self, used_corpora, weights):
        # select a random corpus
        # grab the readers for that corpus
        # consume the next doc from the latest reader
        # assumes readers are open
        while True:
            corpus_name = random.choices(used_corpora, weights=weights)[0]
            corpus_reader = self.readers[corpus_name]
            num_docs, docs, size = next(corpus_reader)
            yield num_docs, docs, size

    def _doc_generator(self):
        # a number of readers per corpora, for each corpora we consume the readers (and thus docs sets)
        # sequentially until exhausted and then reset them
        used_corpora = list(self._corpora_doc_ratios.keys())
        weights = list(self._corpora_doc_ratios.values())
        os.makedirs(self.output_folder, exist_ok=True)

        current_docs = 0
        current_lines = 0
        total_size_in_bytes = 0
        self.logger.info(
            "Generator [%d] is starting to generate [%d] docs",
            self._client_index,
            self.docs_per_client,
        )
        output_file = os.path.join(self.output_folder, f"{self._client_index}.json")
        offset_file = f"{output_file}.offset"
        current_increment = self._offset_increment
        with open(output_file, "wt") as data_file, open(
            offset_file, mode="wt", encoding="utf-8"
        ) as offset_file:
            with CorporaReader(self.readers.values()):
                for num_docs, lines, raw_size_in_bytes in self._reader_generator(
                    used_corpora, weights
                ):
                    if current_docs + num_docs >= self.docs_per_client:
                        self.complete = True
                        # we deliberately don't trim the last batch to get the exact number of documents. This would break
                        # encapsulation and this shouldn't be an issue on larger datasets
                    elif current_docs % 1000 == 0:
                        self.logger.debug(
                            "Generator [%d] has written [%d] docs so far.",
                            self._client_index,
                            current_docs,
                        )
                    # getting chunks of lines which might be less than the batch sizes (cannot be greater) so we output
                    # when we pass the increment and update the offsets. We then shift the increment.
                    if current_lines >= current_increment:
                        print(
                            "%d;%d" % (current_lines, data_file.tell()),
                            file=offset_file,
                        )
                        current_increment += self._offset_increment
                    current_docs += num_docs
                    current_lines += len(lines)
                    total_size_in_bytes += raw_size_in_bytes
                    data_file.writelines([json.dumps(line) + "\n" for line in lines])
                    if self.complete:
                        self.logger.info(
                            "Generator [%d] has completed generating [%d] docs with [%d] bytes.",
                            self._client_index,
                            current_docs,
                            total_size_in_bytes,
                        )
                        FileMetadata.write(
                            self.output_folder,
                            self._client_index,
                            current_docs,
                            total_size_in_bytes,
                        )
                        break

    def _sample_corpus_stats(self):
        corpus_stats = {}
        self.logger.info("Sampling corpora...")
        for integration_name, integration in self._integration_ratios.items():
            for corpus_name in integration["corpora"].keys():
                self.logger.info(
                    "Sampling [%s] docs from corpus [%s]",
                    self._sample_size,
                    corpus_name,
                )
                corpus_reader = self.readers[corpus_name]
                with corpus_reader:
                    sampled_docs = 0
                    total_message_size = 0
                    total_doc_size = 0
                    total_doc_size_with_meta = 0
                    while sampled_docs < self._sample_size:
                        num_docs, docs, message_size = next(corpus_reader)
                        sampled_docs += num_docs
                        line_num = 0
                        total_message_size += message_size
                        for doc in docs:
                            if line_num % 2 == 1:
                                total_doc_size += doc["rally"]["doc_size"]
                                total_doc_size_with_meta += doc["rally"][
                                    "doc_size_with_meta"
                                ]
                            line_num += 1
                    corpus_stats[corpus_name] = {
                        "sampled_docs": sampled_docs,
                        "avg_message_size": total_message_size / sampled_docs,
                        "avg_doc_size": total_doc_size / sampled_docs,
                        "avg_doc_size_with_meta": total_doc_size_with_meta
                        / sampled_docs,
                        "raw_json_ratio": total_doc_size / total_message_size,
                    }
                    self.logger.debug(
                        "Stats for corpora [%s]: [%s]",
                        corpus_name,
                        json.dumps(corpus_stats[corpus_name]),
                    )
        return corpus_stats

    def _init_internal_params(self):
        # avoid zero seeds because of client_index == 0
        seed = (
            (self._client_index + 1) * self._random_seed if self._random_seed else None
        )
        random.seed(seed)
        self.logger.info(
            "Initializing generator [%d/%d] with seed [%d].",
            self._client_index,
            self._client_count,
            seed,
        )

        self.readers = self._create_readers(self._client_count, self._client_index)
        corpus_stats = self._sample_corpus_stats()
        # we will be sampling our corpora based on required doc ratios to satisfy the total gb.
        # Larger corpus need a smaller ratio of lines to satisfy the original user specified ratios in gb
        corpora_ratios = {
            corpus_name: ratio
            for integration_name, integration in self._integration_ratios.items()
            for corpus_name, ratio in integration["corpora"].items()
        }
        corpora_doc_counts = calculate_corpus_counts(
            corpus_stats,
            corpora_ratios,
            self._data_generation_gb,
            self._max_generation_size_gb,
        )
        self._corpora_doc_ratios = calculate_integration_ratios(corpora_doc_counts)
        self.total_docs = sum(corpora_doc_counts.values())
        if self._client_index == 0:
            self.logger.info("Total Docs: [%s]", self.total_docs)
            self.logger.info("Corpora Counts: [%s]", json.dumps(corpora_doc_counts))
            self.logger.info(
                "Corpora Ratios: [%s]", json.dumps(self._corpora_doc_ratios)
            )

        # last client gets a little more from bounds function
        _, self.docs_per_client = bounds(
            self.total_docs, self._client_index, self._client_count
        )


def generate(track, track_data_root, client_index=None, client_count=None):
    generator = CorpusGenerator(
        track=track,
        track_data_root=track_data_root,
        client_index=client_index,
        client_count=client_count,
    )
    # This is determined at startup based on the presence of files
    if generator.complete:
        return True

    # include the `doc_size_with_meta` field per doc used by _sample_corpus_stats() but not for the actual
    # generated docs stored on disk (see below)
    generator.include_doc_size_with_metadata = True
    generator._init_internal_params()

    # don't include doc_size_with_meta field in generated docs that are stored on disk
    generator.include_doc_size_with_metadata = False
    generator._doc_generator()
    return False

import json
import logging
import math
import numbers
import operator
import re

from esrally.track.params import *

class EventBatchDataReader:
    def __init__(self, data_file, batch_size, file_source, collection_name):
        self.data_file = data_file
        self.batch_size = batch_size
        self.file_source = file_source
        self.collection_name = collection_name

    def __enter__(self):
        self.file_source.open(self.data_file, "rt", self.batch_size)
        return self

    def __iter__(self):
        return self

    def __next__(self):
        batch = []
        try:
            docs_in_batch = 0
            while docs_in_batch < self.batch_size:
                try:
                  rows = next(self.file_source)
                  for row in rows:
                    docs_in_batch += 1
                    event_data = json.loads(row)
                    batch.append((event_data['event_type'], event_data['payload']))
                except StopIteration:
                    break
            if docs_in_batch == 0:
                raise StopIteration()
            return self.collection_name, batch
        except OSError:
            logging.getLogger(__name__).exception("Could not read [%s]", self.data_file)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file_source.close()
        return False


class EventIngestParamSource(ParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self.corpora = track.corpora

        if len(self.corpora) == 0:
            raise exceptions.InvalidSyntax(f"There is no document corpus definition for track {track}.")

        self.ingest_percentage = self.float_param(params, name="ingest-percentage", default_value=100, min_value=0, max_value=100)

        try:
            self.batch_size = int(params.get("batch-size", 1000))
            if self.batch_size <= 0:
                raise exceptions.InvalidSyntax("'batch-size' must be positive but was %d" % self.batch_size)
        except ValueError:
            raise exceptions.InvalidSyntax("'batch-size' must be numeric")

        self.param_source = PartitionEventIngestParamSource(
            self.corpora,
            self.batch_size,
            self.ingest_percentage,
            self._params
        )

    def float_param(self, params, name, default_value, min_value, max_value, min_operator=operator.le):
        try:
            value = float(params.get(name, default_value))
            if min_operator(value, min_value) or value > max_value:
                interval_min = "(" if min_operator is operator.le else "["
                raise exceptions.InvalidSyntax(
                    f"'{name}' must be in the range {interval_min}{min_value:.1f}, {max_value:.1f}] but was {value:.1f}"
                )
            return value
        except ValueError:
            raise exceptions.InvalidSyntax(f"'{name}' must be numeric")

    def partition(self, partition_index, total_partitions):
        self.param_source.partition(partition_index, total_partitions)
        return self.param_source

    def params(self):
        raise exceptions.RallyError("Do not use a EventIngestParamSource without partitioning")

class PartitionEventIngestParamSource:
    def __init__(
        self,
        corpora,
        batch_size,
        ingest_percentage,
        original_params=None,
    ):
        self.corpora = corpora
        self.batch_size = batch_size
        self.partitions = []
        self.total_partitions = None
        self.ingest_percentage = ingest_percentage
        self.original_params = original_params
        self.current_event = 0
        self.total_events = 1
        self.infinite = False

    def partition(self, partition_index, total_partitions):
        if self.total_partitions is None:
            self.total_partitions = total_partitions
        elif self.total_partitions != total_partitions:
            raise exceptions.RallyAssertionError(
                f"Total partitions is expected to be [{self.total_partitions}] but was [{total_partitions}]"
            )
        self.partitions.append(partition_index)

    def params(self):
        if self.current_event == 0:
            self._init_event_generator()

        if self.current_event == self.total_events:
            raise StopIteration()
        self.current_event += 1
        param = next(self.event_generator)
        return param

    @property
    def percent_completed(self):
        return self.current_event / self.total_events

    def _init_event_generator(self):
        self.partitions = sorted(self.partitions)
        start_index = self.partitions[0]
        end_index = self.partitions[-1]

        all_events = self._number_of_events(start_index, end_index)
        self.total_events = math.ceil((all_events * self.ingest_percentage) / 100)

        readers = self._create_event_readers(start_index, end_index)
        self.event_generator = self._create_event_generator(chain(*readers))

    def _bounds(self, docs, start_partition_index, end_partition_index):
        return bounds(docs.number_of_documents, start_partition_index, end_partition_index, self.total_partitions, docs.includes_action_and_meta_data)

    def _number_of_events(self, start_partition_index, end_partition_index):
        events = 0
        for corpus in self.corpora:
            for docs in corpus.documents:
                _, num_docs, _ = self._bounds(docs, start_partition_index, end_partition_index)
                events += num_docs
        return events

    def _create_event_readers(self, start_partition_index, end_partition_index):
        readers = []

        for corpus in self.corpora:
            for docs in corpus.documents:
                offset, num_docs, num_lines = self._bounds(docs, start_partition_index, end_partition_index)
                if num_docs > 0:
                    reader = self._create_event_reader(docs, offset, num_lines, num_docs)
                    readers.append(reader)

        return readers

    def _create_event_reader(self, docs, offset, num_lines, num_docs):
        source = Slice(io.MmapSource, offset, num_lines)
        target = None
        if docs.target_index:
            target = docs.target_index
        elif docs.target_data_stream:
            target = docs.target_data_stream

        return EventBatchDataReader(docs.document_file, self.batch_size, source, self._collection_name(target))

    def _collection_name(self, index_name):
        return re.search('behavioral_analytics-events-(.*)', index_name).group(1)

    def _create_event_generator(self, readers):
        for collection_name, batch in readers:
            for event_type, event_payload in batch:
                params = self.original_params.copy()
                params.update({
                    "path": "/_application/analytics/%s/event/%s" % (collection_name, event_type),
                    "method": "POST",
                    "body": event_payload,
                })
                yield params


def register(registry):
  registry.register_param_source("event-ingest-param-source", EventIngestParamSource)

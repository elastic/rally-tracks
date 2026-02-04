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
from esrally import exceptions

"""
Provides a param source for use on the data stream runner. This is a temporary workaround until we have native
data stream support in Rally.
"""


class DataStreamParamSource:
    def __init__(self, track, params, **kwargs):
        self._params = params
        self.infinite = False
        target_data_stream = params.get("data-stream")
        data_stream_definitions = []
        if target_data_stream:
            if isinstance(target_data_stream, str):
                target_data_stream = [target_data_stream]
            for data_stream in target_data_stream:
                data_stream_definitions.append(data_stream)
        elif track.data_streams:
            for data_stream in track.data_streams:
                data_stream_definitions.append(data_stream.name)
        else:
            raise exceptions.InvalidSyntax(f"{params.get('operation-type')} operation targets no data streams")
        self._wait_for_status = track.selected_challenge_or_default.parameters.get("wait-for-status", None)
        self._target_data_stream = iter(data_stream_definitions)

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        data_stream = next(self._target_data_stream)
        params = self._params.copy()
        params["data-stream"] = data_stream
        params["wait-for-status"] = self._wait_for_status
        return params


"""
Provides a param source for use on the create data stream runner. This ensures we only create the data streams which we
need i.e. that will receive data from the targeted corpora through the track parameter "integration_ratios".
"""


class CreateDataStreamParamSource:
    def __init__(self, track, params, **kwargs):
        self._params = params
        self.infinite = False
        integration_ratios = track.selected_challenge_or_default.parameters.get("integration-ratios", None)
        listed_corpora = [
            corpus
            for integration_name, integration in integration_ratios.items()
            for corpus, ratio in integration["corpora"].items()
            if ratio > 0
        ]
        targeted_corpora = [corpus for corpus in track.corpora if corpus.name in listed_corpora]
        # we de-duplicate the list of data streams as more than 1 corpus can use the same data stream
        target_data_stream = list(
            dict.fromkeys([corpus.documents[0].target_data_stream for corpus in targeted_corpora if len(corpus.documents) > 0])
        )
        self._target_data_stream = iter(target_data_stream)

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        data_stream = next(self._target_data_stream)
        params = self._params.copy()
        params["data-stream"] = data_stream
        return params


class SequentialDataStreamParamSource:
    """
    Parameter source for creating a large number of data streams with
    sequential naming (e.g., datastream-0, datastream-1, ...).


    Usage in track.json:
    {
        "name": "create-datastreams",
        "operation": {
        "operation-type": "create-datastream",
        "param-source": "sequential-datastream-source"
        },
        "clients": 8,
        "warmup-iterations": 0,
        "iterations": 10000,
        "params": {
          "data-stream-prefix": "dlm-benchmark",
          "start-index": 0
        }
    }
    """

    def __init__(self, track, params, **kwargs):
        self._params = params
        self._prefix = params.get("data-stream-prefix", "datastream")
        self._start_index = params.get("start-index", 0)
        self._current_index = self._start_index
        self.infinite = False

    def partition(self, partition_index, total_partitions):
        """
        Partition the parameter source across multiple clients.
        Each partition gets a subset of the sequential indices.
        """
        partitioned = SequentialDataStreamParamSource.__new__(SequentialDataStreamParamSource)
        partitioned._params = self._params
        partitioned._prefix = self._prefix
        partitioned._start_index = self._start_index + partition_index
        partitioned._current_index = partitioned._start_index
        partitioned._step = total_partitions
        partitioned.infinite = False
        return partitioned

    def params(self):
        data_stream_name = f"{self._prefix}-{self._current_index}"
        self._current_index += getattr(self, "_step", 1)
        return {**self._params, "data-stream": data_stream_name, "ignore-existing": self._params.get("ignore-existing", False)}


class DLMBulkIndexParamSource:
    """
    Parameter source for bulk indexing to DLM benchmark data streams.
    Generates simple documents and distributes them across dlm-benchmark-* data streams.
    """

    def __init__(self, track, params, **kwargs):
        import time
        from datetime import datetime, timezone

        self._params = params
        self._prefix = params.get("data-stream-prefix", "dlm-benchmark")
        self._data_stream_count = params.get("data-stream-count", 10000)
        self._bulk_size = params.get("bulk-size", 1000)
        self._current_stream = 0
        self.infinite = True  # For continuous indexing

    def partition(self, partition_index, total_partitions):
        """Each client gets a different starting data stream to distribute load evenly."""
        import copy

        partitioned = DLMBulkIndexParamSource.__new__(DLMBulkIndexParamSource)
        partitioned._params = self._params
        partitioned._prefix = self._prefix
        partitioned._data_stream_count = self._data_stream_count
        partitioned._bulk_size = self._bulk_size
        partitioned._current_stream = partition_index % self._data_stream_count
        partitioned._step = total_partitions
        partitioned.infinite = True
        return partitioned

    def params(self):
        import json
        from datetime import datetime, timezone

        # Round-robin through data streams
        data_stream_name = f"{self._prefix}-{self._current_stream}"
        self._current_stream = (self._current_stream + getattr(self, "_step", 1)) % self._data_stream_count

        # Generate bulk request body
        bulk_lines = []
        timestamp = datetime.now(tz=timezone.utc).isoformat()

        for i in range(self._bulk_size):
            # Metadata line
            bulk_lines.append(json.dumps({"create": {"_index": data_stream_name}}))
            # Document line
            doc = {
                "@timestamp": timestamp,
                "message": f"DLM benchmark test message {i}",
                "host": {"hostname": f"host-{i % 100}"},
                "service": {"name": "dlm-benchmark"},
                "log": {"level": "info"},
            }
            bulk_lines.append(json.dumps(doc))

        body = "\n".join(bulk_lines) + "\n"

        return {"body": body, "action-metadata-present": True, "bulk-size": self._bulk_size, "unit": "docs"}

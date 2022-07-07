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
            raise exceptions.InvalidSyntax(
                f"{params.get('operation-type')} operation targets no data streams"
            )
        self._wait_for_status = track.selected_challenge_or_default.parameters.get(
            "wait-for-status", None
        )
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
        integration_ratios = track.selected_challenge_or_default.parameters.get(
            "integration-ratios", None
        )
        listed_corpora = [
            corpus
            for integration_name, integration in integration_ratios.items()
            for corpus, ratio in integration["corpora"].items()
            if ratio > 0
        ]
        targeted_corpora = [
            corpus for corpus in track.corpora if corpus.name in listed_corpora
        ]
        # we de-duplicate the list of data streams as more than 1 corpus can use the same data stream
        target_data_stream = list(
            dict.fromkeys(
                [
                    corpus.documents[0].target_data_stream
                    for corpus in targeted_corpora
                    if len(corpus.documents) > 0
                ]
            )
        )
        self._target_data_stream = iter(target_data_stream)

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        data_stream = next(self._target_data_stream)
        params = self._params.copy()
        params["data-stream"] = data_stream
        return params

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
from shared.parameter_sources.datastream import (
    DataStreamParamSource,
    CreateDataStreamParamSource,
)
from tests.parameter_sources import StaticTrack


def test_read_track_data_streams():
    data_stream_source = DataStreamParamSource(StaticTrack(), params={})
    data_streams = [
        "logs-system.syslog-default",
        "logs-elastic.agent-default",
        "logs-elastic.kafka-default",
    ]
    i = 0
    while True:
        try:
            params = data_stream_source.params()
            assert params["data-stream"] == data_streams[i]
            i += 1
            pass
        except StopIteration:
            break
    assert i == 3


def test_read_data_stream():
    data_stream_source = DataStreamParamSource(
        StaticTrack(), params={"data-stream": "logs-elastic.agent-default"}
    )
    params = data_stream_source.params()
    assert params["data-stream"] == "logs-elastic.agent-default"


def test_read_data_stream_list():
    data_streams = ["test-1", "test-2"]
    data_stream_source = DataStreamParamSource(
        StaticTrack(), params={"data-stream": data_streams}
    )
    i = 0
    while True:
        try:
            params = data_stream_source.params()
            assert params["data-stream"] == data_streams[i]
            i += 1
            pass
        except StopIteration:
            break
    assert i == 2


def test_create_data_stream_list():
    indices = ["logs-system.test", "logs-kafka.test", "logs-system.test"]
    create_data_stream_source = CreateDataStreamParamSource(
        StaticTrack(
            parameters={
                "integration-ratios": {
                    "agent": {"corpora": {"agent-logs": 0.5}},
                    "kafka": {"corpora": {"kafka-logs": 0.25}},
                    "system": {"corpora": {"system-logs": 0.25}},
                }
            }
        ),
        params={},
    )
    i = 0
    while True:
        try:
            params = create_data_stream_source.params()
            assert params["data-stream"] == indices[i]
            i += 1
            pass
        except StopIteration:
            break
    # duplicates should be removed
    assert i == 2


def test_create_no_data_streams():
    create_data_stream_source = CreateDataStreamParamSource(
        StaticTrack(parameters={"integration-ratios": {}}), params={}
    )
    i = 0
    while True:
        try:
            create_data_stream_source.params()
            i += 1
            pass
        except StopIteration:
            break
    assert i == 0

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

from itertools import chain

import pytest
from security.parameter_sources.events_emitter import EventsEmitterParamSource
from tests.parameter_sources import StaticTrack


def test_missing_params():
    with pytest.raises(ValueError) as exc_info:
        EventsEmitterParamSource(
            StaticTrack(parameters={"output-folder": "/tmp/output", "track-id": "123"}),
            params={},
        )
    assert str(exc_info.value) == "Required param 'schema' is not configured"

    with pytest.raises(KeyError) as exc_info:
        EventsEmitterParamSource(
            StaticTrack(parameters={"output-folder": "/tmp/output", "track-id": "123"}),
            params={},
            _test_schema={},
        )
    assert str(exc_info.value) == "'number-of-alerts'"

    with pytest.raises(ValueError) as exc_info:
        EventsEmitterParamSource(
            StaticTrack(parameters={"output-folder": "/tmp/output", "track-id": "123"}),
            params={
                "number-of-alerts": 0,
            },
            _test_schema={},
        )
    assert str(exc_info.value) == "Either param 'rules' or 'queries' must be configured"

    with pytest.raises(ValueError) as exc_info:
        EventsEmitterParamSource(
            StaticTrack(parameters={"output-folder": "/tmp/output", "track-id": "123"}),
            params={
                "number-of-alerts": 0,
                "queries": [],
            },
            _test_schema={},
        )
    assert str(exc_info.value) == "Param 'queries' requires param 'index' to be configured"

    with pytest.raises(ValueError) as exc_info:
        EventsEmitterParamSource(
            StaticTrack(parameters={"output-folder": "/tmp/output", "track-id": "123"}),
            params={
                "number-of-alerts": 0,
                "queries": [],
                "index": "test_index",
            },
            _test_schema={},
        )
    assert str(exc_info.value) == "No valid rules or queries were loaded"


def test_one_query():
    param_source = EventsEmitterParamSource(
        StaticTrack(parameters={"output-folder": "/tmp/output", "track-id": "123"}),
        params={
            "number-of-alerts": 10,
            "queries": [
                "process where process.pid == 12345 or process.pid == 54321",
            ],
            "index": "test_index",
        },
        _test_schema={"process.pid": {"type": "long"}},
    )
    params = param_source.params()
    assert params["request-timeout"] == None
    docs = list(chain(*params["doc-batches"]))
    assert len(docs) == 10

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

from shared.parameter_sources.track_params import TrackParamSource
from tests.parameter_sources import StaticTrack


def test_track_params():
    track_params_source = TrackParamSource(
        StaticTrack(parameters={"output-folder": "/tmp/output", "track-id": "123"}),
        params={"track-id": "234"},
    )
    params = track_params_source.params()
    assert params["output-folder"] == "/tmp/output"
    assert params["track-id"] == "234"

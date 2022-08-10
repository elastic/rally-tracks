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

from shared.track_processors.track_id_generator import TrackIdGenerator
from tests.parameter_sources import StaticTrack


def test_generate_id():
    track_generator = TrackIdGenerator()
    parameters = {
        "raw-data-volume-per-day": "1GB",
        "not-considered-in-hash": "random",
        "random-seed": 13,
        "max-generated-corpus-size": "1GB",
        "data-generation-clients": 2,
        "max-total-download-per-corpus-gb": "1GB",
        "start-date": "now",
        "bulk-start-date": "now-2d",
        "end-date": "now+1d",
        "bulk-end-date": "now",
        "integration-ratios": {
            "system": {"system-logs": 0.4},
            "kafka": {"kafka-logs": 0.6},
        },
        "exclude-properties": {"system": ["container"]},
    }
    static_track = StaticTrack(parameters=parameters)
    track_generator.on_after_load_track(static_track)
    assert (
        static_track.selected_challenge.parameters["track-id"]
        == "46bf445bdccc86dc4816bd49316e1fc9"
    )
    parameters["not-considered-in-hash"] = "random-2"
    static_track_2 = StaticTrack(parameters=copy.deepcopy(parameters))
    track_generator.on_after_load_track(static_track_2)
    assert (
        static_track.selected_challenge.parameters["track-id"]
        == static_track_2.selected_challenge.parameters["track-id"]
    )
    parameters["raw-data-volume-per-day"] = "2GB"
    parameters["not-considered-in-hash"] = "random"
    static_track_3 = StaticTrack(parameters=copy.deepcopy(parameters))
    track_generator.on_after_load_track(static_track_3)
    assert (
        static_track.selected_challenge.parameters["track-id"]
        != static_track_3.selected_challenge.parameters["track-id"]
    )

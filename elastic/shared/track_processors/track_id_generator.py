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

import hashlib
import json
import logging


class TrackIdGenerator:
    track_id_hash_parameters = [
        "raw-data-volume-per-day",
        "random-seed",
        "max-generated-corpus-size",
        "data-generation-clients",
        "max-total-download-per-corpus-gb",
        "start-date",
        "bulk-start-date",
        "end-date",
        "bulk-end-date",
        "integration-ratios",
        "exclude-properties",
    ]

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def on_after_load_track(self, track):
        hash_parameters = {}
        for hash_param in self.track_id_hash_parameters:
            if hash_param in track.selected_challenge_or_default.parameters:
                hash_parameters[hash_param] = track.selected_challenge_or_default.parameters[hash_param]
        track.selected_challenge_or_default.parameters["track-id"] = hashlib.md5(
            json.dumps(hash_parameters, sort_keys=True).encode("utf-8")
        ).hexdigest()
        self.logger.info(
            "Track id is [%s]",
            track.selected_challenge_or_default.parameters["track-id"],
        )

    def on_prepare_track(self, track, data_root_dir):
        return []

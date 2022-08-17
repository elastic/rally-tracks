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

from shared import parameter_sources
from shared.runners.ilm import create_ilm
from shared.runners.pipelines import create_pipeline

from endpoint.track_processors.assets_loader import AssetsLoader


def register(registry):
    registry.register_param_source(
        "add-asset-paths", parameter_sources.add_asset_paths
    )

    registry.register_runner("create-ilm", create_ilm, async_runner=True)

    registry.register_runner("create-pipeline", create_pipeline, async_runner=True)

    registry.register_track_processor(AssetsLoader())

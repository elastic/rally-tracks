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
from shared.parameter_sources.datastream import (
    CreateDataStreamParamSource,
    DataStreamParamSource,
)
from shared.parameter_sources.initial_indices import InitialIndicesParamSource
from shared.parameter_sources.processed import ProcessedCorpusParamSource
from shared.parameter_sources.templates import (
    ComponentTemplateParamSource,
    ComposableTemplateParamSource,
)
from shared.parameter_sources.track_params import TrackParamSource
from shared.parameter_sources.workflow_selector import WorkflowSelectorParamSource
from shared.runners import datastream, snapshot
from shared.runners.bulk import RawBulkIndex
from shared.runners.ilm import create_ilm
from shared.runners.pipelines import create_pipeline
from shared.runners.remote_cluster import ConfigureRemoteCluster, FollowIndexRunner
from shared.runners.slm import create_slm
from shared.runners.update_custom_templates import update_custom_templates
from shared.schedulers.indexing import TimestampThrottler
from shared.schedulers.query import WorkflowScheduler
from shared.track_processors import data_generator
from shared.track_processors.track_id_generator import TrackIdGenerator


def register(registry):
    registry.register_param_source("initial-indices-source", InitialIndicesParamSource)
    registry.register_param_source("add-track-path", parameter_sources.add_track_path)

    registry.register_param_source("component-template-source", ComponentTemplateParamSource)
    registry.register_param_source("composable-template-source", ComposableTemplateParamSource)

    registry.register_param_source("datastream-source", DataStreamParamSource)
    registry.register_param_source("create-datastream-source", CreateDataStreamParamSource)
    registry.register_runner("create-datastream", datastream.create, async_runner=True)
    registry.register_runner("compression-statistics", datastream.compression_stats, async_runner=True)
    registry.register_runner("check-datastream", datastream.check_health, async_runner=True)
    registry.register_runner("rollover-datastream", datastream.rollover, async_runner=True)
    registry.register_runner("set-shards-datastream", datastream.shards, async_runner=True)
    registry.register_runner("update-custom-templates", update_custom_templates, async_runner=True)

    registry.register_param_source("processed-source", ProcessedCorpusParamSource)

    registry.register_runner("create-ilm", create_ilm, async_runner=True)
    registry.register_runner("create-slm", create_slm, async_runner=True)

    registry.register_runner("create-pipeline", create_pipeline, async_runner=True)

    registry.register_runner("raw-bulk", RawBulkIndex(), async_runner=True)

    registry.register_runner("mount-searchable-snapshot", snapshot.mount, async_runner=True)

    registry.register_scheduler("workflow-scheduler", WorkflowScheduler)
    registry.register_scheduler("timestamp-throttler", TimestampThrottler)

    registry.register_param_source("workflow-selector", WorkflowSelectorParamSource)

    registry.register_param_source("track-params-source", TrackParamSource)

    registry.register_track_processor(TrackIdGenerator())
    registry.register_track_processor(data_generator.DataGenerator())

    registry.register_runner("configure-remote-cluster", ConfigureRemoteCluster(), async_runner=True)
    registry.register_runner("follow-index", FollowIndexRunner(), async_runner=True)

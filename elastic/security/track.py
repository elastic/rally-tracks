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
from shared.parameter_sources.workflow_selector import WorkflowSelectorParamSource
from shared.parameter_sources.templates import (
    ComponentTemplateParamSource,
    ComposableTemplateParamSource,
)
from shared.runners import datastream
from shared.runners.ilm import create_ilm
from shared.runners.pipelines import create_pipeline
from shared.schedulers.indexing import TimestampThrottler
from shared.schedulers.query import WorkflowScheduler

from security.parameter_sources.events_emitter import EventsEmitterParamSource
from security.runners.emit_events import emit_events


def register(registry):
    registry.register_param_source(
        "add-track-path", parameter_sources.add_track_path
    )
    registry.register_param_source(
        "component-template-source", ComponentTemplateParamSource
    )
    registry.register_param_source(
        "composable-template-source", ComposableTemplateParamSource
    )
    registry.register_param_source(
        "events-emitter-source", EventsEmitterParamSource
    )

    registry.register_runner(
        "check-datastream", datastream.check_health, async_runner=True
    )
    registry.register_runner(
        "rollover-datastream", datastream.rollover, async_runner=True
    )
    registry.register_runner(
        "set-shards-datastream", datastream.shards, async_runner=True
    )
    registry.register_runner(
        "emit-events", emit_events, async_runner=True
    )

    registry.register_runner("create-ilm", create_ilm, async_runner=True)
    registry.register_runner("create-pipeline", create_pipeline, async_runner=True)

    registry.register_scheduler("workflow-scheduler", WorkflowScheduler)
    registry.register_scheduler("timestamp-throttler", TimestampThrottler)

    registry.register_param_source("workflow-selector", WorkflowSelectorParamSource)

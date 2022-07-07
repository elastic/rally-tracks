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

from shared.parameter_sources.templates import (
    ComponentTemplateParamSource,
    ComposableTemplateParamSource,
    remove_pipelines,
    remove_routing_shards,
)
from tests.parameter_sources import StaticTrack


def test_component_template_load():
    template_source = ComponentTemplateParamSource(StaticTrack(), params={})
    params = template_source.params()
    assert len(params["templates"]) == 1
    assert params["templates"][0][0] == "logs-endpoint.events.process-mappings"


def test_composable_template_load():
    template_source = ComposableTemplateParamSource(StaticTrack(), params={})
    params = template_source.params()
    assert len(params["templates"]) == 1
    assert params["templates"][0][0] == "logs-endpoint.events.process"


def test_removal_of_default_pipeline():
    component_template_source = ComponentTemplateParamSource(
        StaticTrack(), params={"remove-pipelines": True}
    )
    params = component_template_source.params()
    assert len(params["templates"]) == 1
    assert params["templates"][0][0] == "logs-endpoint.events.process-mappings"
    assert (
        "default_pipeline"
        not in params["templates"][0][1]["template"]["settings"]["index"]
    )
    composable_template_source = ComposableTemplateParamSource(
        StaticTrack(), params={"remove-pipelines": True}
    )
    params = composable_template_source.params()
    assert len(params["templates"]) == 1
    assert params["templates"][0][0] == "logs-endpoint.events.process"
    assert (
        "default_pipeline"
        not in params["templates"][0][1]["template"]["settings"]["index"]
    )


def test_removal_of_routing_shards():
    component_template_source = ComponentTemplateParamSource(
        StaticTrack(), params={"remove-routing-shards": True}
    )
    params = component_template_source.params()
    assert len(params["templates"]) == 1
    assert params["templates"][0][0] == "logs-endpoint.events.process-mappings"
    assert (
        "number_of_routing_shards"
        not in params["templates"][0][1]["template"]["settings"]["index"]
    )
    composable_template_source = ComposableTemplateParamSource(
        StaticTrack(), params={"remove-routing-shards": True}
    )
    params = composable_template_source.params()
    assert len(params["templates"]) == 1
    assert params["templates"][0][0] == "logs-endpoint.events.process"
    assert (
        "number_of_routing_shards"
        not in params["templates"][0][1]["template"]["settings"]["index"]
    )


def test_remove_pipelines():
    content = remove_pipelines(
        {
            "template": {
                "settings": {
                    "index": {"default_pipeline": "test", "final_pipeline": "test"}
                }
            }
        },
        False,
    )
    assert content["template"]["settings"]["index"]["default_pipeline"] == "test"
    assert content["template"]["settings"]["index"]["final_pipeline"] == "test"
    content = remove_pipelines(
        {
            "template": {
                "settings": {
                    "index": {"default_pipeline": "test", "final_pipeline": "test"}
                }
            }
        },
        True,
    )
    assert "default_pipeline" not in content["template"]["settings"]["index"]
    assert "final_pipeline" not in content["template"]["settings"]["index"]


def test_remove_routing_shards():
    content = remove_pipelines(
        {"template": {"settings": {"index": {"number_of_routing_shards": 30}}}}, False
    )
    assert content["template"]["settings"]["index"]["number_of_routing_shards"] == 30
    content = remove_routing_shards(
        {"template": {"settings": {"index": {"number_of_routing_shards": 30}}}}, True
    )
    assert "number_of_routing_shards" not in content["template"]["settings"]["index"]

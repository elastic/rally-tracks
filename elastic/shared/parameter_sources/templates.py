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

from esrally.track.params import (
    CreateComposableTemplateParamSource,
    CreateComponentTemplateParamSource,
)


class ComponentTemplateParamSource(CreateComponentTemplateParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self.template_definitions = [
            (template[0], process_template(template[1], params))
            for template in self.template_definitions
        ]


class ComposableTemplateParamSource(CreateComposableTemplateParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self.template_definitions = [
            (template[0], process_template(template[1], params))
            for template in self.template_definitions
        ]


def process_template(content, params):
    content = remove_pipelines(content, params.get("remove-pipelines", False))
    return remove_routing_shards(content, params.get("remove-routing-shards", False))


def remove_pipelines(content, remove):
    if not remove:
        return content
    if (
        "template" in content
        and "settings" in content["template"]
        and "index" in content["template"]["settings"]
    ):
        if "default_pipeline" in content["template"]["settings"]["index"]:
            del content["template"]["settings"]["index"]["default_pipeline"]
        if "final_pipeline" in content["template"]["settings"]["index"]:
            del content["template"]["settings"]["index"]["final_pipeline"]
    return content


def remove_routing_shards(content, remove):
    if not remove:
        return content
    if (
        "template" in content
        and "settings" in content["template"]
        and "index" in content["template"]["settings"]
    ):
        if "number_of_routing_shards" in content["template"]["settings"]["index"]:
            del content["template"]["settings"]["index"]["number_of_routing_shards"]
    return content

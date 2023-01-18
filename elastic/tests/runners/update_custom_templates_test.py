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

from unittest import mock

import pytest
from shared.runners.update_custom_templates import update_custom_templates
from tests import as_future


@mock.patch("elasticsearch.Elasticsearch")
@pytest.mark.asyncio
async def test_update_custom_templates(es):
    es.cluster.put_component_template.return_value = as_future({})
    templates = {
        "component_templates": [
            {
                "name": "logs-kafka.log@custom",
                "component_template": {
                    "template": {"settings": {}},
                    "_meta": {"package": {"name": "kafka"}, "managed_by": "fleet", "managed": "true"},
                },
            },
            {
                "name": "logs-kafka.log@package",
                "component_template": {
                    "template": {
                        "settings": {"index": {"lifecycle": {"name": "logs"}, "codec": "best_compression"}},
                        "mappings": {
                            "properties": {
                                "cloud": {
                                    "properties": {
                                        "availability_zone": {"ignore_above": 1024, "type": "keyword"},
                                    }
                                }
                            }
                        },
                        "_meta": {"package": {"name": "kafka"}, "managed_by": "fleet", "managed": "true"},
                    }
                },
            },
        ]
    }

    es.cluster.get_component_template.return_value = as_future(templates)

    params = {
        "body": {
            "template": {
                "settings": {
                    "index": {
                        "number_of_replicas": 0,
                        "number_of_shards": 1,
                    }
                },
                "mappings": {"runtime": {"rally.doc_size": {"type": "long"}, "rally.message_size": {"type": "long"}}},
            }
        }
    }

    original_template = templates["component_templates"][0]["component_template"]
    merged_template = {**original_template, **params["body"]}

    await update_custom_templates(es, params)
    # logs-kafka.log@package template should not be interfered with, so we expect
    # a single call to `put_component_template`
    es.cluster.put_component_template.assert_called_once_with(name="logs-kafka.log@custom", body=merged_template)

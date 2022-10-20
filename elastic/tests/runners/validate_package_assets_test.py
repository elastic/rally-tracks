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
from shared.runners.validate_package_assets import validate_package_assets
from tests import as_future


@mock.patch("elasticsearch.Elasticsearch")
@pytest.mark.asyncio
async def test_validate_package_assets_raises_exception_if_missing_packages(es):
    installed = ["apache", "kafka", "mysql", "nginx", "postgresql", "redis"]
    missing = ["system"]
    templates = {"index_templates": [{"index_template": {"_meta": {"package": {"name": p}}}} for p in installed]}
    es.indices.get_index_template.return_value = as_future(templates)

    params = {"packages": ["apache", "kafka", "mysql", "nginx", "postgresql", "redis", "system"], "asset-types": "index-templates"}
    with pytest.raises(BaseException) as e:
        await validate_package_assets(es, params)

    assert f"Index templates missing for packages: {missing}" in str(e)


@mock.patch("elasticsearch.Elasticsearch")
@pytest.mark.asyncio
async def test_validate_package_assets_with_all_packages_installed(es):
    installed = ["apache", "kafka", "mysql", "nginx", "postgresql", "redis", "system"]
    templates = {"index_templates": [{"index_template": {"_meta": {"package": {"name": p}}}} for p in installed]}
    es.indices.get_index_template.return_value = as_future(templates)

    params = {"packages": ["apache", "kafka", "mysql", "nginx", "postgresql", "redis", "system"], "asset-types": "index-templates"}
    assert await validate_package_assets(es, params)

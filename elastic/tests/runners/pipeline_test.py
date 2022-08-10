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

import os
from unittest import mock
import pytest
from tests import as_future
from shared.runners.pipelines import create_pipeline


@mock.patch("elasticsearch.Elasticsearch")
@pytest.mark.asyncio
async def test_pipeline(es):
    es.ingest.put_pipeline.return_value = as_future({})
    # simulate "track-path" as added by param source and "policies" set by the user
    params = {
        "track-path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "logs"),
        "pipelines": "../tests/runners/resources/pipelines"
    }
    ops, _ = await create_pipeline(
        es, params
    )
    assert ops == 1

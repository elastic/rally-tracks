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
from esrally import exceptions
from shared.runners.dlm import (
    put_lifecycle
)
from tests import as_future


class TestPutLifecycle:
    """Tests for put_lifecycle function"""

    @mock.patch("elasticsearch.Elasticsearch")
    @pytest.mark.asyncio
    async def test_put_lifecycle_with_all_params(self, es):
        """Test configuring lifecycle with retention and enabled parameters"""
        # Mock responses
        es.indices.get_data_stream.return_value = as_future(
            {"data_streams": [{"name": "logs-test-default"}, {"name": "logs-test-staging"}]}
        )
        es.perform_request.return_value = as_future({})

        params = {"data-stream": "logs-test-*", "data_retention": "7d", "enabled": True}

        ops, unit = await put_lifecycle(es, params)

        assert ops == 2
        assert unit == "ops"

        # Verify get_data_stream was called correctly
        es.indices.get_data_stream.assert_called_once_with(name="logs-test-*")

        # Verify perform_request was called twice with correct parameters
        assert es.perform_request.call_count == 2
        calls = es.perform_request.call_args_list

        # Check first call
        assert calls[0][1]["method"] == "PUT"
        assert calls[0][1]["path"] == "/_data_stream/logs-test-default/_lifecycle"
        assert calls[0][1]["body"] == {"data_retention": "7d", "enabled": True}

        # Check second call
        assert calls[1][1]["method"] == "PUT"
        assert calls[1][1]["path"] == "/_data_stream/logs-test-staging/_lifecycle"
        assert calls[1][1]["body"] == {"data_retention": "7d", "enabled": True}

    @mock.patch("elasticsearch.Elasticsearch")
    @pytest.mark.asyncio
    async def test_put_lifecycle_with_empty_config(self, es):
        """Test configuring lifecycle with no parameters (empty config)"""
        es.indices.get_data_stream.return_value = as_future({"data_streams": [{"name": "logs-kafka-default"}]})
        es.perform_request.return_value = as_future({})

        params = {"data-stream": "logs-kafka-default"}

        ops, unit = await put_lifecycle(es, params)

        assert ops == 1
        assert unit == "ops"

        # Verify empty dict is sent as body (not None)
        es.perform_request.assert_called_once()
        call_args = es.perform_request.call_args
        assert call_args[1]["body"] == {}

    @mock.patch("elasticsearch.Elasticsearch")
    @pytest.mark.asyncio
    async def test_put_lifecycle_with_retention_only(self, es):
        """Test configuring lifecycle with only retention parameter"""
        es.indices.get_data_stream.return_value = as_future({"data_streams": [{"name": "logs-nginx-default"}]})
        es.perform_request.return_value = as_future({})

        params = {"data-stream": "logs-nginx-default", "data_retention": "30d"}

        ops, unit = await put_lifecycle(es, params)

        assert ops == 1
        assert unit == "ops"

        call_args = es.perform_request.call_args
        assert call_args[1]["body"] == {"data_retention": "30d"}

    @mock.patch("elasticsearch.Elasticsearch")
    @pytest.mark.asyncio
    async def test_put_lifecycle_missing_required_param(self, es):
        """Test that missing data-stream parameter raises error"""
        params = {"data_retention": "7d"}

        with pytest.raises(exceptions.DataError):
            await put_lifecycle(es, params)

    @mock.patch("elasticsearch.Elasticsearch")
    @pytest.mark.asyncio
    async def test_put_lifecycle_get_data_stream_fails(self, es):
        """Test error handling when get_data_stream fails"""
        es.indices.get_data_stream.return_value = as_future(exception=Exception("Connection failed"))

        params = {"data-stream": "logs-test-*"}

        with pytest.raises(Exception, match="Connection failed"):
            await put_lifecycle(es, params)

    @mock.patch("elasticsearch.Elasticsearch")
    @pytest.mark.asyncio
    async def test_put_lifecycle_perform_request_fails(self, es):
        """Test error handling when perform_request fails"""
        es.indices.get_data_stream.return_value = as_future({"data_streams": [{"name": "logs-test-default"}]})
        es.perform_request.return_value = as_future(exception=Exception("API error"))

        params = {"data-stream": "logs-test-default"}

        with pytest.raises(Exception, match="API error"):
            await put_lifecycle(es, params)

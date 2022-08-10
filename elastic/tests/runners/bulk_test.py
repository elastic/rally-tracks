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
from shared.runners.bulk import RawBulkIndex
from tests import as_future


@mock.patch("elasticsearch.Elasticsearch")
@pytest.mark.asyncio
async def test_detailed_stats(es, tmp_path):
    es.bulk.return_value = as_future(
        {
            "took": 30,
            "ingest_took": 20,
            "errors": True,
            "items": [
                {
                    "index": {
                        "_index": "test",
                        "_type": "_doc",
                        "_id": "1",
                        "_version": 1,
                        "result": "created",
                        "_shards": {"total": 2, "successful": 1, "failed": 0},
                        "created": True,
                        "status": 201,
                        "_seq_no": 0,
                    }
                },
                {
                    "update": {
                        "_index": "test",
                        "_type": "_doc",
                        "_id": "2",
                        "_version": 2,
                        "result": "updated",
                        "_shards": {"total": 2, "successful": 1, "failed": 0},
                        "status": 200,
                        "_seq_no": 1,
                    }
                },
                {
                    "index": {
                        "_index": "test",
                        "_type": "_doc",
                        "_id": "3",
                        "_version": 1,
                        "result": "noop",
                        "_shards": {"total": 2, "successful": 0, "failed": 2},
                        "created": False,
                        "status": 500,
                        "_seq_no": -2,
                    }
                },
                {
                    "index": {
                        "_index": "test",
                        "_type": "_doc",
                        "_id": "4",
                        "_version": 1,
                        "result": "noop",
                        "_shards": {"total": 2, "successful": 1, "failed": 1},
                        "created": False,
                        "status": 500,
                        "_seq_no": -2,
                    }
                },
                {
                    "index": {
                        "_index": "test",
                        "_type": "_doc",
                        "_id": "5",
                        "_version": 1,
                        "result": "created",
                        "_shards": {"total": 2, "successful": 1, "failed": 0},
                        "created": True,
                        "status": 201,
                        "_seq_no": 4,
                    }
                },
                {
                    "update": {
                        "_index": "test",
                        "_type": "_doc",
                        "_id": "6",
                        "_version": 2,
                        "result": "noop",
                        "_shards": {"total": 2, "successful": 0, "failed": 2},
                        "status": 404,
                        "_seq_no": 5,
                    }
                },
            ],
        }
    )
    bulk = RawBulkIndex()
    bulk_params = {
        "body": [
            '{ "index" : { "_index" : "test", "_type" : "_doc" } }',
            '{"message" : "test example", "@timestamp": "2020-01-01T00:00:00.000Z"}',
            '{ "update" : { "_index" : "test", "_type" : "_doc", "_id: "2" } }',
            '{"message" : "test example", "@timestamp": "2020-01-01T00:01:00.000Z"}',
            '{ "index" : { "_index" : "test", "_type" : "_doc" } }',
            '{"message" : "test example", "@timestamp": "2020-01-01T00:02:00.000Z"}',
            '{ "index" : { "_index" : "test", "_type" : "_doc" } }',
            '{"message" : "test example", "@timestamp": "2020-01-01T00:03:00.000Z"}',
            '{ "index" : { "_index" : "test", "_type" : "_doc" } }',
            '{"message" : "test example", "@timestamp": "2020-01-01T00:04:00.000Z"}',
            '{ "update" : { "_index" : "test", "_type" : "_doc", "_id: "3" } }',
            '{"message" : "test example", "@timestamp": "2020-01-01T00:05:00.000Z"}',
        ],
        "action-metadata-present": True,
        "bulk-size": 6,
        "unit": "docs",
        "detailed-results": True,
        "index": "test",
        "param-source-stats": {
            "raw-size-bytes": 200,
            "event-time-span": 300,
            "relative-time": 2,
            "index-lag": -298,
            "max-timestamp": "2020-01-01T00:05:00.000Z",
            "min-timestamp": "2020-01-01T00:00:00.000Z",
        },
    }
    result = await bulk(es, bulk_params)
    assert result["index"] == "test"
    assert result["took"] == 30
    assert result["ingest_took"] == 20
    assert result["weight"] == 6
    assert result["unit"] == "docs"
    assert result["success"] == False
    assert result["error-count"] == 3
    assert result["error-type"] == "bulk"
    assert result["raw-size-bytes"] == 200
    assert result["event-time-span"] == 300
    assert result["relative-time"] == 2
    assert result["index-lag"] == result["relative-time"] - result["event-time-span"]
    assert result["min-timestamp"] == "2020-01-01T00:00:00.000Z"
    assert result["max-timestamp"] == "2020-01-01T00:05:00.000Z"

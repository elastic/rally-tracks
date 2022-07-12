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
import json
import os
from unittest import mock
import pytest
from shared.runners.datastream import compression_stats, rollover, create
from tests import as_future


def search(index, body):
    if "total_doc_size" in body["aggs"]:
        return as_future(
            {
                "took": 5704,
                "timed_out": False,
                "_shards": {"total": 2, "successful": 2, "skipped": 0, "failed": 0},
                "hits": {
                    "total": {"value": 10000, "relation": "gte"},
                    "max_score": None,
                    "hits": [],
                },
                "aggregations": {"total_doc_size": {"value": 4.00000000000e11}},
            }
        )
    return as_future(
        {
            "took": 6955,
            "timed_out": False,
            "_shards": {"total": 2, "successful": 2, "skipped": 0, "failed": 0},
            "hits": {
                "total": {"value": 10000, "relation": "gte"},
                "max_score": None,
                "hits": [],
            },
            "aggregations": {"total_msg_size": {"value": 40000000000}},
        }
    )


count_response = {
    "stream-with-message": as_future(
        {
            "count": 200000000,
            "_shards": {"total": 2, "successful": 2, "skipped": 0, "failed": 0},
        }
    ),
    "stream-without-message": as_future(
        {
            "count": 200000000,
            "_shards": {"total": 2, "successful": 2, "skipped": 0, "failed": 0},
        }
    ),
    "empty-stream": as_future(
        {
            "count": 0,
            "_shards": {"total": 2, "successful": 2, "skipped": 0, "failed": 0},
        }
    ),
}

message_count_response = {
    "stream-with-message": count_response["stream-with-message"],
    "stream-without-message": as_future(
        {
            "count": 0,
            "_shards": {"total": 2, "successful": 2, "skipped": 0, "failed": 0},
        }
    ),
    "empty-stream": count_response["empty-stream"],
}


def count(index, body={}):
    if not body:
        return count_response[index]
    else:
        return message_count_response[index]


@mock.patch("elasticsearch.Elasticsearch")
@pytest.mark.asyncio
async def test_data_stream_rollover(es):
    cwd = os.path.dirname(__file__)
    with open(
        os.path.join(cwd, "resources", "data_streams", "logs.json")
    ) as data_stream_file:
        es.indices.get_data_stream.return_value = as_future(json.load(data_stream_file))
    es.indices.rollover.return_value = as_future(
        {
            "acknowledged": True,
            "shards_acknowledged": True,
            "old_index": "old_index",
            "new_index": "new_index",
            "rolled_over": True,
            "dry_run": False,
            "conditions": {"[max_docs: 0]": True},
        }
    )
    result = await rollover(
        es, {"conditions": {"max_docs": 0}, "data-stream": "logs-*"}
    )
    assert result[0] == 13


@mock.patch("elasticsearch.Elasticsearch")
@pytest.mark.asyncio
async def test_data_stream_create(es):
    cwd = os.path.dirname(__file__)
    with open(
        os.path.join(cwd, "resources", "data_streams", "logs.json")
    ) as data_stream_file:
        es.indices.get_data_stream.return_value = as_future(json.load(data_stream_file))
    es.indices.create_data_stream.return_value = as_future({"acknowledged": True})
    result = await create(
        es, {"data-stream": "logs-kafka.log-default", "ignore-existing": True}
    )
    assert result[0] == 0
    result = await create(
        es, {"data-stream": "logs-mongo.log-default", "ignore-existing": True}
    )
    assert result[0] == 1
    result = await create(
        es, {"data-stream": "logs-kafka.log-default", "ignore-existing": False}
    )
    assert result[0] == 1


@mock.patch("elasticsearch.Elasticsearch")
@pytest.mark.asyncio
async def test_data_stream_stats(es):
    es.indices.stats.return_value = as_future(
        {
            "_shards": {"total": 4, "successful": 4, "failed": 0},
            "_all": {
                "primaries": {
                    "docs": {"count": 200000000, "deleted": 0},
                    "store": {"size_in_bytes": 100000000000, "reserved_in_bytes": 0},
                }
            },
        }
    )
    es.search.side_effect = search
    es.count.side_effect = count
    data_streams = ["stream-with-message", "stream-without-message", "empty-stream"]
    complete = [True, False, False]
    weights = [11, 7, 0]
    stats = {
        "stream-with-message": {
            "doc_count": 200000000,
            "index_size": 100000000000,
            "reserved_size": 0,
            "doc_size": 400000000000.0,
            "docs_with_message": 200000000,
            "json_to_index_ratio": 0.25,
            "avg_doc_size": 2000.0,
            "message_size": 40000000000,
            "avg_message_size": 200.0,
            "raw_to_json_ratio": 10.0,
            "raw_to_index_ratio": 2.5,
        },
        "stream-without-message": {
            "doc_count": 200000000,
            "docs_with_message": 0,
            "index_size": 100000000000,
            "reserved_size": 0,
            "doc_size": 400000000000.0,
            "json_to_index_ratio": 0.25,
            "avg_doc_size": 2000.0,
        },
        "empty-stream": {},
    }
    for i, data_stream in enumerate(data_streams):
        result = await compression_stats(es, {"data-stream": data_stream})
        assert len(result.keys()) == 4
        assert data_stream == result["data_stream"]
        assert result["weight"] == weights[i]
        assert result["data_stream_stats"] == stats[data_stream]
        assert result["complete_message_stats"] == complete[i]

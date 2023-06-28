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

import asyncio
import logging

import elasticsearch
from shared.utils.track import mandatory

"""
Provides operations on data streams. These are a temporary workaround until we have native data stream support in Rally.
"""


async def create(es, params):
    ops = 0
    data_stream = mandatory(params, "data-stream", "create-datastream")
    ignore_existing = params.get("ignore-existing", False)
    logger = logging.getLogger(__name__)
    create_data_stream = data_stream
    if ignore_existing:
        existing = []
        try:
            response = await es.indices.get_data_stream(name=data_stream)
            existing = [ds_stream["name"] for ds_stream in response["data_streams"]]
        except elasticsearch.exceptions.NotFoundError:
            pass
        logger.debug("Existing data streams: [%s]", existing)
        if data_stream in existing:
            create_data_stream = None
    if create_data_stream:
        logger.debug("Create data stream: [%s]", data_stream)
        await es.indices.create_data_stream(name=data_stream)
        ops += 1
    return ops, "ops"


class DeleteRemoteDataStream:
    multi_cluster = True

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def __call__(self, multi_es, params):
        """
        Deletes specified datastreams from all clusters
        """
        for ops, (cluster_name, cluster_client) in enumerate(multi_es.items(), start=1):
            data_stream = params["data-stream"]
            try:
                self.logger.info("Deleting data stream: [%s] in cluster [%s]", data_stream, cluster_name)
                await cluster_client.indices.delete_data_stream(name=data_stream)
            except elasticsearch.ElasticsearchException as e:
                msg = f"Failed to delete datastream [{data_stream}]; [{e}]"
                self.logger.error("Deleting data stream: [%s] in cluster [%s]", data_stream, cluster_name)
                raise BaseException(msg, e)
        return ops, "ops"

    def __repr__(self, *args, **kwargs):
        return "delete-remote-datastream"


async def check_health(es, params):
    data_stream = mandatory(params, "data-stream", "check-datastream")
    ops = 0
    wait_for_status = params.get("wait-for-status", "green")
    wait_period = params.get("recheck-wait-period", 1)
    is_healthy = False
    while not is_healthy:
        is_healthy = True
        ops += 1
        response = await es.indices.get_data_stream(name=data_stream)
        for ds_stream in response["data_streams"]:
            if ds_stream["status"].lower() != wait_for_status:
                is_healthy = False
                await asyncio.sleep(wait_period)
                break
    return ops, "ops"


async def rollover(es, params):
    logger = logging.getLogger(__name__)
    data_stream = mandatory(params, "data-stream", "rollover-datastream")
    conditions = params.get("conditions", {"max_docs": 0})
    ops = 0
    # expand the data_streams into a list as we cant use wildcard in rollover
    response = await es.indices.get_data_stream(name=data_stream)
    for ds_stream in response["data_streams"]:
        rollover_response = await es.indices.rollover(alias=ds_stream["name"], body={"conditions": conditions})
        logger.debug(
            "Rolled over [%s] - old index: [%s], new index: [%s]",
            rollover_response["old_index"],
            rollover_response["new_index"],
        )
        ops += 1
    return ops, "ops"


async def shards(es, params):
    number_of_replicas = mandatory(params, "number-of-replicas", "set-data-stream-shards")
    data_stream = mandatory(params, "data-stream", "set-shards-datastream")
    await es.indices.put_settings(
        body={"number_of_replicas": number_of_replicas},
        index=data_stream,
    )
    return 1, "ops"


async def compression_stats(es, params):
    data_stream = mandatory(params, "data-stream", "compression-statistics")
    data_stream_stats = {}
    # used to indicate if we have complete message field statistics
    complete_message_stats = False
    response = await es.count(index=data_stream)
    total_count = response["count"]
    if total_count > 0:
        response = await es.indices.stats(index=data_stream)
        ds_doc_count = response["_all"]["primaries"]["docs"]["count"]
        ds_index_size = response["_all"]["primaries"]["store"]["size_in_bytes"]
        reserved_size = response["_all"]["primaries"]["store"]["reserved_in_bytes"]
        response = await es.search(
            index=data_stream,
            body={
                "aggs": {
                    "total_doc_size": {"sum": {"field": "rally.doc_size"}},
                },
                "size": 0,
            },
        )
        ds_doc_size = response["aggregations"]["total_doc_size"]["value"]
        # not all docs have messages, only calculate if we have message on every field
        # note - we use message_size as we may have removed message in processing
        response = await es.count(
            index=data_stream,
            body={"query": {"exists": {"field": "rally.message_size"}}},
        )
        message_count = response["count"]
        data_stream_stats = {
            "doc_count": ds_doc_count,
            "docs_with_message": message_count,
            "index_size": ds_index_size,
            "reserved_size": reserved_size,
            "doc_size": ds_doc_size,
            "json_to_index_ratio": ds_index_size / ds_doc_size,
            "avg_doc_size": ds_doc_size / total_count,
        }
        if total_count == message_count:
            response = await es.search(
                index=data_stream,
                body={
                    "aggs": {
                        "total_msg_size": {"sum": {"field": "rally.message_size"}},
                    },
                    "size": 0,
                },
            )
            ds_msg_size = response["aggregations"]["total_msg_size"]["value"]
            data_stream_stats["message_size"] = ds_msg_size
            data_stream_stats["avg_message_size"] = ds_msg_size / total_count
            data_stream_stats["raw_to_json_ratio"] = ds_doc_size / ds_msg_size
            data_stream_stats["raw_to_index_ratio"] = ds_index_size / ds_msg_size
            complete_message_stats = True
        else:
            logger = logging.getLogger(__name__)
            # justifies a warning
            logger.warning(
                "Unable to fetch message statistics for data stream [%s] - [%s] docs, [%s] have message "
                "- field docs missing message fields in corpus",
                data_stream,
                total_count,
                message_count,
            )
    return {
        "data_stream": data_stream,
        "data_stream_stats": data_stream_stats,
        "weight": len(data_stream_stats.keys()),
        "complete_message_stats": complete_message_stats,
    }

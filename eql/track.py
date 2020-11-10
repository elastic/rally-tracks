import elasticsearch
import logging

async def eql(es, params):
    logger = logging.getLogger(__name__)
    logger.info("Provided params [%s].", params)
    await es.transport.perform_request(
            "POST",
            elasticsearch.client.utils._make_path(params.get("index"), "_eql", "search"),
            body=params.get("body"),
        )

def register(registry):
    registry.register_runner("eql", eql, async_runner=True)

import logging


async def eql(es, params):
    logger = logging.getLogger(__name__)
    logger.info("Provided params [%s].", params)
    await es.eql.search(
            params.get("index"),
            body=params.get("body"),
            request_timeout=params.get("request-timeout")
        )


def register(registry):
    registry.register_runner("eql", eql, async_runner=True)

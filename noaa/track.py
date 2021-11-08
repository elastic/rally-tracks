import logging


async def sql(es, params):
    logger = logging.getLogger(__name__)
    logger.info("Provided params [%s].", params)
    
    body = params.get("body")
    # default page_timeout is not suited for benchmarks as it keeps the scroll contexts open for 45s
    if 'page_timeout' not in body:
        body['page_timeout'] = '100ms'

    await es.sql.query(
            body=body,
            request_timeout=params.get("request-timeout")
        )


def register(registry):
    registry.register_runner("sql", sql, async_runner=True)

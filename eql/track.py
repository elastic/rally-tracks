

async def eql(es, params):
    if cluster := params.get("cluster", ""):
        cluster += ":"

    await es.eql.search(
            index=cluster + params.get("index"),
            body=params.get("body"),
            request_timeout=params.get("request-timeout")
        )


def register(registry):
    registry.register_runner("eql", eql, async_runner=True)

async def sql(es, params):    
    await es.sql.query(
        body=params["body"]
    )


def register(registry):
    registry.register_runner("sql", sql, async_runner=True)
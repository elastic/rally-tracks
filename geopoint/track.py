def refresh(es, params):
    es.indices.refresh(index=params.get("index", "_all"))


def register(registry):
    registry.register_runner("refresh", refresh)

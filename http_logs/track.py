def refresh(es, params):
    es.indices.refresh(index=params.get("index", "_all"))


def register(registry):
    # as a side-effect, check and move data for the standard case.
    registry.register_runner("refresh", refresh)

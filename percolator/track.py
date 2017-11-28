def percolate(es, params):
    es.percolate(
        index="queries",
        doc_type="content",
        body=params["body"]
    )
    return 1, "ops"


def refresh(es, params):
    es.indices.refresh(index=params.get("index", "_all"))


def register(registry):
    registry.register_runner("percolate", percolate)
    registry.register_runner("refresh", refresh)

def percolate(es, params):
    es.percolate(
        index="queries",
        doc_type="content",
        body=params["body"]
    )
    return 1, "ops"


def register(registry):
    registry.register_runner("percolate", percolate)

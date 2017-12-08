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
    try:
        major, minor, patch, _ = registry.meta_data["rally_version"]
    except AttributeError:
        # We must be below Rally 0.8.2 (did not provide version metadata).
        # register "refresh" for older versions of Rally. Newer versions have support out of the box.
        registry.register_runner("refresh", refresh)
    registry.register_runner("percolate", percolate)

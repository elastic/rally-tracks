def percolate(es, params):
    es.transport.perform_request("GET", "/queries/content/_percolate", body=params["body"])
    return 1, "ops"


def register(registry):
    registry.register_runner("percolate", percolate)

def reindex(es, params):
  result = es.reindex(body=params.get("body"), request_timeout=params.get("request_timeout"))
  return result["total"], "docs"

def register(registry):
  registry.register_runner("reindex", reindex)

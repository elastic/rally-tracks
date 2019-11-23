def reindex(es, params):
  es.reindex(body=params.get("body"), request_timeout=params.get("request_timeout"))

def register(registry):
  registry.register_runner("reindex", reindex)

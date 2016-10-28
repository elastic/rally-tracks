import random


def random_country(indices, params):
    return {
        "body": {
            "query": {
                "term": {
                    "country_code": "%s" % random.choice(params["countries"])
                }
            }
        },
        "index": None,
        "type": None,
        "use_request_cache": False
    }


def register(registry):
    registry.register_param_source("term-param-source", random_country)
import random


def knn_param_source(track, params, **kwargs):
    # choose a suitable index: if there is only one defined for this track
    # choose that one, but let the user always override index
    random.seed(31)
    if len(track.indices) == 1:
        default_index = track.indices[0].name
    else:
        default_index = "_all"

    index_name = params.get("index", default_index)

    return {
        "body": {
            "knn": {
                "field": "image-vector",
                "query_vector": params.get("query-vector", [random.uniform(-1.0, 1.0) for _ in range(96)]),
                "k": params.get("k", 10),
                "num_candidates": params.get("num-candidates", 100),
            },
            "_source": False,
        },
        "index": index_name,
        "cache": params.get("cache", False),
    }


def register(registry):
    registry.register_param_source("knn-param-source", knn_param_source)

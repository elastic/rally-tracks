import json
import os

class KnnParamSource:
    def __init__(self, track, params, **kwargs):
        # choose a suitable index: if there is only one defined for this track
        # choose that one, but let the user always override index
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._index_name = params.get("index", default_index)
        self._cache = params.get("cache", False)
        self._exact_scan = params.get("exact", False)
        self._params = params

        cwd = os.path.dirname(__file__)
        with open(os.path.join(cwd, "queries.json"), "r") as file:
            lines = file.readlines()
        self._queries = [json.loads(line) for line in lines]
        self._iters = 0
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        result = {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "size": self._params.get("k", 10)
        }

        if self._exact_scan:
            result["body"] = {
                "query": {
                    "script_score": {
                        "query": { "match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query, 'vector') + 1.0",
                            "params": { "query": self._queries[self._iters] }
                        }
                    }
                },
                "_source": False
            }
        else:
            result["body"] = {
                "knn": {
                    "field": "vector",
                    "query_vector": self._queries[self._iters],
                    "k": self._params.get("k", 10),
                    "num_candidates": self._params.get("num-candidates", 100)
                },
                "_source": False
            }
        self._iters += 1
        return result


def register(registry):
    registry.register_param_source("knn-param-source", KnnParamSource)

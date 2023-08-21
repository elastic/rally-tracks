import json
import os

QUERIES_FILENAME: str = "queries.json"


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
        self._params = params
        self._queries = []

        cwd = os.path.dirname(__file__)
        with open(os.path.join(cwd, QUERIES_FILENAME), "r") as queries_file:
            for vector_query in queries_file:
                self._queries.append(json.loads(vector_query))
        self._iters = 0
        self._maxIters = len(self._queries)
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        result = {"index": self._index_name, "cache": self._params.get("cache", False), "size": self._params.get("k", 10)}

        result["body"] = {
            "knn": {
                "field": "emb",
                "query_vector": self._queries[self._iters],
                "k": self._params.get("k", 10),
                "num_candidates": self._params.get("num-candidates", 50),
            },
            "_source": False,
        }
        if "filter" in self._params:
            result["body"]["knn"]["filter"] = self._params["filter"]

        self._iters += 1
        if self._iters >= self._maxIters:
            self._iters = 0
        return result


def register(registry):
    registry.register_param_source("knn-param-source", KnnParamSource)

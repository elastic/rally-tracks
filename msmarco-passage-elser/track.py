import itertools
import json
import os


class WeightedTermsParamsSource:
    def __init__(self, track, params, **kwargs):
        # choose a suitable index: if there is only one defined for this track
        # choose that one, but let the user always override index
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._index_name = params.get("index", default_index)
        self._cache = params.get("cache", False)
        self._size = params.get("size", 10)
        self._field = params.get("field", "ml.tokens")
        self._tokens_file = params.get("tokens-source", "elser-query-tokens.json")
        self._num_terms = params.get("num-terms", 10)
        self._track_total_hits = params.get("track_total_hits", False)
        self._params = params

        cwd = os.path.dirname(__file__)
        with open(os.path.join(cwd, self._tokens_file), "r") as file:
            self._query_tokens = json.load(file)

        self._iters = 0

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        query = self._query_tokens[self._iters]
        if self._num_terms > len(query):
            raise Exception(f"The requested number of terms {self._num_terms} cannot be satisfied by the query with {len(query)} tokens")

        result = {"index": self._index_name, "cache": self._cache, "size": self._size}
        result["body"] = {
            "query": {
                "bool": {
                    "should": [
                        {"term": {f"{self._field}": {"value": f"{key}", "boost": value}}}
                        for key, value in itertools.islice(query.items(), self._num_terms)
                    ]
                }
            },
            "track_total_hits": self._track_total_hits,
        }
        self._iters = (self._iters + 1) % len(self._query_tokens)

        return result


def register(registry):
    registry.register_param_source("weighted-terms-param-source", WeightedTermsParamsSource)

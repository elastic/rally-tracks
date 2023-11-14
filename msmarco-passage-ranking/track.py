import json
import os


class QueryParamsSource:
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
        self._text_field = params.get("text_field", "text")
        self._text_expansion_field = params.get("text_expansion_field", "text_expansion")
        self._query_file = params.get("query_source", "queries.json")
        self._query_strategy = params.get("query_strategy", "bm25")
        self._track_total_hits = params.get("track_total_hits", False)
        self._params = params

        cwd = os.path.dirname(__file__)
        with open(os.path.join(cwd, self._query_file), "r") as file:
            self._queries = json.load(file)
        self._iters = 0

    def partition(self, partition_index, total_partitions):
        return self

    def generate_weighted_terms_query(self, query_expansion, boost=1.0):
        return {
            "query": {
                "bool": {
                    "should": [
                        {"term": {f"{self._text_expansion_field}": {"value": f"{key}", "boost": value}}}
                        for key, value in query_expansion.items()
                    ],
                    "boost": boost,
                }
            }
        }

    def generate_bm25_query(self, query, boost=1.0):
        return {"query": {"match": {f"{self._text_field}": {"query": query, "boost": boost}}}}

    def generate_combine_bm25_weighted_terms_query(self, query, query_boost, query_expansion, query_expansion_boost):
        return {
            "query": {
                "bool": {
                    "should": [
                        self.generate_bm25_query(query, query_boost)["query"],
                        self.generate_weighted_terms_query(query_expansion, query_expansion_boost)["query"],
                    ]
                }
            }
        }

    def params(self):
        query_doc = self._queries[self._iters]
        if self._query_strategy == "bm25":
            query = self.generate_bm25_query(query_doc["query"], 1)
        elif self._query_strategy == "text_expansion":
            query = self.generate_weighted_terms_query(query_doc["query_expansion"], 1)
        elif self._query_strategy == "hybrid":
            query = self.generate_combine_bm25_weighted_terms_query(query_doc["query"], 1, query_doc["query_expansion"], 1)
        else:
            raise Exception(f"The query strategy \\`{self._query_strategy}]\\` is not implemented")

        self._iters = (self._iters + 1) % len(self._queries)
        return {
            "index": self._index_name,
            "cache": self._cache,
            "size": self._size,
            "track_total_hits": self._track_total_hits,
            "body": query,
        }


def register(registry):
    registry.register_param_source("query_param_source", QueryParamsSource)

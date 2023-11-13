import json
import logging
import os


def generate_weighted_terms_query(field, query_expansion, boost=1.0):
    return {
        "query": {
            "bool": {
                "should": [
                    {"term": {f"{field}": {"value": f"{key}", "boost": value}}}
                    for key, value in query_expansion.items()
                ],
                "boost": boost,
            }
        }
    }


def generate_weighted_terms_pruned_query(field, query_expansion, pruning_strategy, boost=1.0):
    return {
        "query": {
            "weighted_terms": {
                f"{field}": {
                    "terms": query_expansion,
                    "query_strategy": pruning_strategy
                }
            }
        }
    }


def generate_bm25_query(field, query, boost=1.0):
    return {"query": {"match": {f"{field}": {"query": query, "boost": boost}}}}


def generate_combine_bm25_weighted_terms_query(query_field, query, query_boost, query_expansion_field, query_expansion,
                                               query_expansion_boost):
    return {
        "query": {
            "bool": {
                "should": [
                    generate_bm25_query(query_field, query, query_boost)["query"],
                    generate_weighted_terms_query(query_expansion_field, query_expansion, query_expansion_boost)[
                        "query"],
                ]
            }
        }
    }


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
        self._text_expansion_field = params.get("text_expansion_field", "text_expansion_elser")
        self._query_file = params.get("query_source", "queries.json")
        self._query_strategy = params.get("query_strategy", "bm25")
        self._pruning_strategy = params.get("pruning_strategy", None)
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
        query_obj = self._queries[self._iters]
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


# For each query this will generate both the weighted terms query and a pruned version of the same query.
# The two queries can then be executed and used to gauge the accuracy of the pruned query.
class WeightedRecallParamSource:
    def __init__(self, track, params, **kwargs):
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._query_file = params.get("query_source", "queries.json")
        self._index_name = params.get("index", default_index)
        self._cache = params.get("cache", False)
        self._params = params
        self._queries = []
        self.infinite = True

        cwd = os.path.dirname(__file__)
        with open(os.path.join(cwd, self._query_file), "r") as file:
            self._queries = json.load(file)

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        return {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "top_k": self._params.get("top_k", 10),
            "num_candidates": self._params.get("num_candidates", 100),
            "queries": self._queries,
            "text_expansion_field": self._params.get("text_expansion_field", "text_expansion"),
        }


class WeightedTermsRecallRunner:
    async def __call__(self, es, params):
        recall_total = 0
        exact_total = 0
        min_recall = params["top_k"]

        for query in params["queries"]:
            weighted_terms_result = await es.search(
                body=generate_weighted_terms_query(params['text_expansion_field'], query["query_expansion"], 1),
                index=params["index"],
                request_cache=params["cache"],
                size=params["top_k"],
            )
            pruned_weighted_terms_result = await es.search(
                body=generate_weighted_terms_pruned_query(params['text_expansion_field'],
                                                          query["query_expansion"],
                                                          "ONLY_SCORE_LOW_FREQUENCY_TERMS",
                                                          1),
                index=params["index"],
                request_cache=params["cache"],
                size=params["num_candidates"],
            )
            weighted_terms_hits = {hit["_id"] for hit in weighted_terms_result["hits"]["hits"]}
            pruned_weighted_terms_hits = {hit["_id"] for hit in pruned_weighted_terms_result["hits"]["hits"]}
            current_recall = len(weighted_terms_hits.intersection(pruned_weighted_terms_hits))
            recall_total += current_recall
            exact_total += len(weighted_terms_hits)
            min_recall = min(min_recall, current_recall)


        logging.getLogger(__name__).info(
            "top_k=%d, num_candidates=%d, avg_recall=%.3f",
            params["top_k"], params["num_candidates"], float(recall_total / exact_total))
        return (
            {
                "avg_recall": recall_total / exact_total,
                "min_recall": min_recall,
                "top_k": params["top_k"],
                "num_candidates": params["num_candidates"],
            }
            if exact_total > 0
            else None
        )

    def __repr__(self, *args, **kwargs):
        return "weighted_terms_recall"


def register(registry):
    registry.register_param_source("query_param_source", QueryParamsSource)
    registry.register_param_source("weighted_terms_recall_param_source", WeightedRecallParamSource)
    registry.register_runner("weighted_terms_recall", WeightedTermsRecallRunner(), async_runner=True)

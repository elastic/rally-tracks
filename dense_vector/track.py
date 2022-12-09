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
        result = {"index": self._index_name, "cache": self._params.get("cache", False), "size": self._params.get("k", 10)}

        if self._exact_scan:
            result["body"] = {
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query, 'vector') + 1.0",
                            "params": {"query": self._queries[self._iters]},
                        },
                    }
                },
                "_source": False,
            }
        else:
            result["body"] = {
                "knn": {
                    "field": "vector",
                    "query_vector": self._queries[self._iters],
                    "k": self._params.get("k", 10),
                    "num_candidates": self._params.get("num-candidates", 100),
                },
                "_source": False,
            }
        self._iters += 1
        return result


# For each query this will generate both the knn query and the equivalent
# score script query. The two queries can then be executed and used
# to gauge the accuracy of the knn query.
class KnnRecallParamSource:
    def __init__(self, track, params, **kwargs):
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._index_name = params.get("index", default_index)
        self._cache = params.get("cache", False)
        self._params = params

        cwd = os.path.dirname(__file__)
        with open(os.path.join(cwd, "queries.json"), "r") as file:
            lines = file.readlines()
        self._queries = [json.loads(line) for line in lines]
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        return {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "size": self._params.get("k", 10),
            "num_candidates": self._params.get("num-candidates", 100),
            "queries": self._queries,
        }


# Used in tandem with the KnnRecallParamSource. This executes both a knn query
# and an equivalent score script query. Results are then compared to gauge
# the accuracy of the knn query.
class KnnRecallRunner:
    async def __call__(self, es, params):
        recall_total = 0
        exact_total = 0
        min_recall = params["size"]

        for query in params["queries"]:
            knn_result = await es.search(
                body={
                    "knn": {
                        "field": "vector",
                        "query_vector": query,
                        "k": params["size"],
                        "num_candidates": params["num_candidates"],
                    },
                    "_source": False,
                },
                index=params["index"],
                request_cache=params["cache"],
                size=params["size"],
            )
            script_result = await es.search(
                body={
                    "query": {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": "cosineSimilarity(params.query, 'vector') + 1.0",
                                "params": {"query": query},
                            },
                        }
                    },
                    "_source": False,
                },
                index=params["index"],
                request_cache=params["cache"],
                size=params["size"],
            )
            knn_hits = {hit["_id"] for hit in knn_result["hits"]["hits"]}
            script_hits = {hit["_id"] for hit in script_result["hits"]["hits"]}
            current_recall = len(knn_hits.intersection(script_hits))
            recall_total += current_recall
            exact_total += len(script_hits)
            min_recall = min(min_recall, current_recall)

        return (
            {
                "avg_recall": recall_total / exact_total,
                "min_recall": min_recall,
                "k": params["size"],
                "num_candidates": params["num_candidates"],
            }
            if exact_total > 0
            else None
        )

    def __repr__(self, *args, **kwargs):
        return "knn-recall"


def register(registry):
    registry.register_param_source("knn-param-source", KnnParamSource)
    registry.register_param_source("knn-recall-param-source", KnnRecallParamSource)
    registry.register_runner("knn-recall", KnnRecallRunner(), async_runner=True)

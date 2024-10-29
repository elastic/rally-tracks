import bz2
import json
import os
import statistics
import logging
from typing import Any, List

logger = logging.getLogger(__name__)
QUERIES_FILENAME: str = "queries.json.bz2"
TRUE_KNN_FILENAME: str = "open_ai_true_top_1000.json.bz2"

def compute_percentile(data: List[Any], percentile):
    size = len(data)
    if size <= 0:
        return None
    sorted_data = sorted(data)
    index = int(round(percentile * size / 100)) - 1
    return sorted_data[max(min(index, size - 1), 0)]

def get_rescore_query(vec, window_size):
    return {
        "window_size": window_size,
        "query": {
            "query_weight": 0,
            "rescore_query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "double value = dotProduct(params.query_vector, 'emb'); return sigmoid(1, Math.E, -value);",
                        "params": {"query_vector": vec},
                    },
                }
            },
        },
    }

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
        with bz2.open(os.path.join(cwd, QUERIES_FILENAME), "r") as queries_file:
            for vector_query in queries_file:
                self._queries.append(json.loads(vector_query))
        self._iters = 0
        self._maxIters = len(self._queries)
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        result = {"index": self._index_name, "cache": self._params.get("cache", False), "size": self._params.get("k", 10)}
        num_candidates = self._params.get("num-candidates", 50)
        num_rescore = self._params.get("num-rescore", 0)
        query_vec = self._queries[self._iters]
        global_rescore = self._params.get("global-rescore", False)
        if global_rescore:
            result["body"] = {
                "knn": {
                    "field": "emb",
                    "query_vector": query_vec,
                    "k": max(result["size"], num_rescore),
                    "num_candidates": max(num_candidates, num_rescore),
                },
                "_source": False
            }
            if num_rescore > 0:
                result["body"]["rescore"] = get_rescore_query(query_vec, num_rescore)
            if "filter" in self._params:
                result["body"]["knn"]["filter"] = self._params["filter"]
        else:
            knn_query = {"knn":{
                "field": "emb",
                "query_vector": query_vec,
                "k": max(result["size"], num_rescore),
                "num_candidates": max(num_candidates, num_rescore),
            }}
            if "filter" in self._params:
                knn_query["filter"] = self._params["filter"]
            if num_rescore > 0:
                knn_query = {"script_score": {
                    "query": knn_query,
                    "script": {
                        "source": "double value = dotProduct(params.query_vector, 'emb'); return sigmoid(1, Math.E, -value);",
                        "params": {"query_vector": query_vec},
                    },
                }}
            result["body"] = {"query": knn_query, "_source": False}
        self._iters += 1
        if self._iters >= self._maxIters:
            self._iters = 0
        return result

class KnnVectorStore:
    def __init__(self):
        cwd = os.path.dirname(__file__)
        self._query_nearest_neighbor_docids = []
        self._queries = []
        with bz2.open(os.path.join(cwd, TRUE_KNN_FILENAME), "r") as queries_file:
            for docids in queries_file:
                self._query_nearest_neighbor_docids.append(json.loads(docids))
        with bz2.open(os.path.join(cwd, QUERIES_FILENAME), "r") as queries_file:
            for vector_query in queries_file:
                self._queries.append(json.loads(vector_query))

    def get_query_vectors(self) -> List[List[float]]:
        return self._queries
    
    def get_neighbors_for_query(self, query_id: int, size: int) -> List[str]:
        if (query_id < 0) or (query_id >= len(self._query_nearest_neighbor_docids)):
            raise ValueError(f"Unknown query with id: '{query_id}' provided")
        if (size < 0) or (size > len(self._query_nearest_neighbor_docids[query_id])):
            raise ValueError(f"Invalid size: '{size}' provided for query with id: '{query_id}'")
        return self._query_nearest_neighbor_docids[query_id][:size]

class KnnRecallParamSource:
    def __init__(self, track, params, **kwargs):
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._index_name = params.get("index", default_index)
        self._cache = params.get("cache", False)
        self._params = params
        self.infinite = True
        cwd = os.path.dirname(__file__)

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        return {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "size": self._params.get("k", 10),
            "num_candidates": self._params.get("num-candidates", 50),
            "num_rescore": self._params.get("num-rescore", 0),
            "global_rescore": self._params.get("global-rescore", False),
            "knn_vector_store": KnnVectorStore()
        }

# Used in tandem with the KnnRecallParamSource.
# reads the queries, executes knn search and compares the results with the true nearest neighbors
class KnnRecallRunner:

    def get_knn_query(self, query_vec, k, num_candidates, global_rescore, num_rescore):
        result_body = {}
        if global_rescore:
            result_body = {
                "knn": {
                    "field": "emb",
                    "query_vector": query_vec,
                    "k": max(k, num_rescore),
                    "num_candidates": max(num_candidates, num_rescore),
                },
                "_source": False
            }
            if num_rescore > 0:
                result_body["rescore"] = get_rescore_query(query_vec, num_rescore) 
        else:
            knn_query = {"knn":{
                "field": "emb",
                "query_vector": query_vec,
                "k": max(k, num_rescore),
                "num_candidates": max(num_candidates, num_rescore),
            }}
            if num_rescore > 0:
                knn_query = {"script_score": {
                    "query": knn_query,
                    "script": {
                        "source": "double value = dotProduct(params.query_vector, 'emb'); return sigmoid(1, Math.E, -value);",
                        "params": {"query_vector": query_vec},
                    },
                }}
            result_body = {"query": knn_query, "_source": False}
        return result_body 


    async def __call__(self, es, params):
        k = params["size"]
        num_candidates = params["num_candidates"]
        index = params["index"]
        request_cache = params["cache"]
        recall_total = 0
        exact_total = 0
        min_recall = k
        max_recall = 0

        knn_vector_store: KnnVectorStore = params["knn_vector_store"]
        for query_id, query_vector in enumerate(knn_vector_store.get_query_vectors()):
            knn_body = self.get_knn_query(query_vector, k, num_candidates, params["global_rescore"], params["num_rescore"])
            knn_body["_source"] = False
            knn_body["docvalue_fields"] = ["docid"]
            knn_result = await es.search(
                body=knn_body,
                index=index,
                request_cache=request_cache,
                size=k,
            )
            knn_hits = [hit["fields"]["docid"][0] for hit in knn_result["hits"]["hits"]]
            true_neighbors = knn_vector_store.get_neighbors_for_query(query_id, k)[:k]
            current_recall = len(set(knn_hits).intersection(set(true_neighbors)))
            recall_total += current_recall
            exact_total += len(true_neighbors)
            min_recall = min(min_recall, current_recall)
            max_recall = max(max_recall, current_recall)
        to_return = {
                "avg_recall": recall_total / exact_total,
                "min_recall": min_recall,
                "max_recall": max_recall,
                "k": k,
                "num_candidates": num_candidates,
                "global_rescore": params["global_rescore"],
                "num_rescore": params["num_rescore"]
            }
        logger.info(f"Recall results: {to_return}")
        return (to_return)

    def __repr__(self, *args, **kwargs):
        return "knn-recall"


def register(registry):
    registry.register_param_source("knn-param-source", KnnParamSource)
    registry.register_param_source("knn-recall-param-source", KnnRecallParamSource)
    registry.register_runner("knn-recall", KnnRecallRunner(), async_runner=True)

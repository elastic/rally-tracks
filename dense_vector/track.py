import json
import logging
import os
from collections import defaultdict
from functools import lru_cache


logger = logging.getLogger(__name__)


class KnnVectorStore:

    def __init__(self, _query_vectors: dict[str, list[float]], _exact_neighbors: dict[str, list[str]]):
        self._query_vectors: dict[str, list[float]] = _query_vectors
        self._exact_neighbors: dict[str, list[str]] = _exact_neighbors

    def get_query_vectors(self) -> dict[str, list[float]]:
        return self._query_vectors

    def get_neighbors_for_query(self, query_id: str) -> list[str]:
        if query_id not in self._exact_neighbors:
            raise ValueError(f"query_id not found in the precomputed list")
        return self._exact_neighbors[query_id]

    @classmethod
    @lru_cache(maxsize=1)
    async def from_queries_files(cls, queries_file: str, index: str, max_size: int, client) -> "KnnVectorStore":
        if not (os.path.exists(queries_file) and os.path.isfile(queries_file)):
            raise ValueError(f"Provided queries file %s does not exist or is not a file" % queries_file)
        query_vectors: dict[str, list[float]]
        with open(queries_file, 'r') as f:
            logger.info(f"Start computing exact neighbors for %s" % queries_file)
            lines = f.readlines()
            query_vectors = {_index: json.loads(vector) for _index, vector in enumerate(lines)}
            exact_neighbors = await KnnVectorStore.extract_exact_neighbors(query_vectors, index, max_size, client)
            logger.info(f"Done computing exact neighbors")
            return KnnVectorStore(query_vectors, exact_neighbors)

    @staticmethod
    async def extract_exact_neighbors(query_vectors: dict[str, list[float]], index: str, max_size: int, client) -> dict[str, list[str]]:
        exact_neighbors: dict[str, list[str]] = defaultdict(list)
        for query_id, query_vector in query_vectors.items():
            script_query = await client.search(
                body={
                    "query": {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": "cosineSimilarity(params.query, 'vector') + 1.0",
                                "params": {"query": query_vector},
                            },
                        }
                    },
                    "_source": False,
                },
                index=index,
                size=max_size,
            )
            neighbors = [hit["_id"] for hit in script_query["hits"]["hits"]]
            exact_neighbors[query_id] = neighbors
        return exact_neighbors


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
        self._queries = []

        cwd = os.path.dirname(__file__)
        with open(os.path.join(cwd, "queries.json"), "r") as file:
            for line in file:
                self._queries.append(json.loads(line))
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
        if self._iters >= len(self._queries):
            self._iters = 0
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
        self._queries = []
        self.infinite = True
        self._queries_file = "queries.json"

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        return {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "size": self._params.get("k", 10),
            "num_candidates": self._params.get("num-candidates", 100),
            "queries_file": self._queries_file,
        }


# Used in tandem with the KnnRecallParamSource. This executes both a knn query
# and an equivalent score script query. Results are then compared to gauge
# the accuracy of the knn query.
class KnnRecallRunner:
    async def __call__(self, es, params):
        knn_vector_store: KnnVectorStore = await KnnVectorStore.from_queries_files(
            params["queries_files"],
            params["index"],
            params["size"],
            es
        )
        recall_total = 0
        exact_total = 0
        min_recall = params["size"]

        for query_id, query_vector in knn_vector_store.get_query_vectors().items():
            knn_result = await es.search(
                body={
                    "knn": {
                        "field": "vector",
                        "query_vector": query_vector,
                        "k": params["size"],
                        "num_candidates": params["num_candidates"],
                    },
                    "_source": False,
                },
                index=params["index"],
                request_cache=params["cache"],
                size=params["size"],
            )
            knn_hits = [hit["_id"] for hit in knn_result["hits"]["hits"]]
            script_hits = knn_vector_store.get_neighbors_for_query(query_id)
            current_recall = len(set(knn_hits).intersection(set(script_hits)))
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

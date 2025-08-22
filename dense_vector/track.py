import functools
import json
import logging
import os
import statistics
from collections import defaultdict
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def extract_vector_operations_count(knn_result):
    vector_operations_count = 0
    profile = knn_result["profile"]
    for shard in profile["shards"]:
        assert len(shard["dfs"]["knn"]) == 1
        knn_search = shard["dfs"]["knn"][0]
        if "vector_operations_count" in knn_search:
            vector_operations_count += knn_search["vector_operations_count"]
    return vector_operations_count


def compute_percentile(data: List[Any], percentile):
    size = len(data)
    if size <= 0:
        return None
    sorted_data = sorted(data)
    index = int(round(percentile * size / 100)) - 1
    return sorted_data[max(min(index, size - 1), 0)]


def load_query_vectors(queries_file) -> Dict[int, List[float]]:
    if not (os.path.exists(queries_file) and os.path.isfile(queries_file)):
        raise ValueError(f"Provided queries file '{queries_file}' does not exist or is not a file")
    query_vectors: Dict[int, List[float]]
    with open(queries_file, "r") as f:
        logger.debug(f"Reading query vectors from '{queries_file}'")
        lines = f.readlines()
        query_vectors = {_index: json.loads(vector) for _index, vector in enumerate(lines)}
        logger.debug(f"Finished reading query vectors from '{queries_file}'")
    return query_vectors


async def extract_exact_neighbors(
    query_vector: List[float], index: str, max_size: int, vector_field: str, request_cache: bool, client
) -> List[str]:
    script_query = {
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": f"cosineSimilarity(params.query, '{vector_field}') + 1.0",
                    "params": {"query": query_vector},
                },
            }
        }
    }
    script_result = await client.search(
        body=script_query,
        index=index,
        request_cache=request_cache,
        size=max_size,
    )
    return [hit["_id"] for hit in script_result["hits"]["hits"]]


class KnnVectorStore:
    @staticmethod
    def empty_store():
        return defaultdict(lambda: defaultdict(list))

    def __init__(self, queries_file: str, vector_field: str):
        assert queries_file and vector_field
        self._query_vectors = load_query_vectors(queries_file)
        self._vector_field = vector_field
        self._store = KnnVectorStore.empty_store()

    async def get_neighbors_for_query(self, index: str, query_id: int, size: int, request_cache: bool, client) -> List[str]:
        try:
            logger.debug(f"Fetching exact neighbors for {query_id} from in-memory store")
            exact_neighbors = self._store[index][query_id]
            if not exact_neighbors or len(exact_neighbors) < size:
                logger.debug(f"Query vector with id {query_id} not cached or has fewer then {size} requested results - computing neighbors")
                self._store[index][query_id] = await self.load_exact_neighbors(index, query_id, size, request_cache, client)
                logger.debug(f"Finished computing exact neighbors for {query_id} - it's now cached!")
            return self._store[index][query_id]
        except Exception as ex:
            logger.exception(f"Failed to compute nearest neighbors for '{query_id}'. Returning empty results instead.", ex)
            return []

    async def load_exact_neighbors(self, index: str, query_id: int, max_size: int, request_cache: bool, client):
        if query_id not in self._query_vectors:
            raise ValueError(f"Unknown query with id: '{query_id}' provided")
        return await extract_exact_neighbors(self._query_vectors[query_id], index, max_size, self._vector_field, request_cache, client)

    def invalidate_all(self):
        logger.info("Invalidating all entries from knn-vector-store")
        self._store = KnnVectorStore.empty_store()

    def get_query_vectors(self) -> Dict[int, List[float]]:
        if len(self._query_vectors) == 0:
            raise ValueError("Query vectors have not been initialized.")
        return self._query_vectors

    @classmethod
    @functools.lru_cache(maxsize=1)
    def get_instance(cls, queries_file: str, vector_field):
        logger.info(f"Initializing KnnVectorStore for queries file: '{queries_file}' and vector field: '{vector_field}'")
        return KnnVectorStore(queries_file, vector_field)


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
        self._vector_field = "vector"

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
                            "source": f"cosineSimilarity(params.query, '{self._vector_field}') + 1.0",
                            "params": {"query": self._queries[self._iters]},
                        },
                    }
                }
            }
        else:
            result["body"] = {
                "knn": {
                    "field": self._vector_field,
                    "query_vector": self._queries[self._iters],
                    "k": self._params.get("k", 10),
                    "num_candidates": self._params.get("num-candidates", 100),
                }
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
        self.infinite = True
        self._target_k = 1_000
        cwd = os.path.dirname(__file__)
        self._queries_file: str = os.path.join(cwd, "queries.json")
        self._vector_field: str = "vector"

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        return {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "size": self._params.get("k", 10),
            "num_candidates": self._params.get("num-candidates", 100),
            "target_k": self._target_k,
            "knn_vector_store": KnnVectorStore.get_instance(self._queries_file, self._vector_field),
            "invalidate_vector_store": self._params.get("invalidate-vector-store", False),
        }


# Used in tandem with the KnnRecallParamSource. This executes both a knn query
# and an equivalent score script query. Results are then compared to gauge
# the accuracy of the knn query.
class KnnRecallRunner:
    async def __call__(self, es, params):
        k = params["size"]
        num_candidates = params["num_candidates"]
        index = params["index"]
        request_cache = params["cache"]
        target_k = max(params["target_k"], k)
        recall_total = 0
        exact_total = 0
        min_recall = k
        nodes_visited = []

        knn_vector_store: KnnVectorStore = params["knn_vector_store"]
        invalidate_vector_store: bool = params["invalidate_vector_store"]
        if invalidate_vector_store:
            knn_vector_store.invalidate_all()
        for query_id, query_vector in knn_vector_store.get_query_vectors().items():
            knn_result = await es.search(
                body={
                    "knn": {
                        "field": "vector",
                        "query_vector": query_vector,
                        "k": k,
                        "num_candidates": num_candidates,
                    },
                    "_source": False,
                    "profile": True,
                },
                index=index,
                request_cache=request_cache,
                size=k,
            )
            knn_hits = [hit["_id"] for hit in knn_result["hits"]["hits"]]
            script_hits = await knn_vector_store.get_neighbors_for_query(index, query_id, target_k, request_cache, es)
            script_hits = script_hits[:k]
            vector_operations_count = extract_vector_operations_count(knn_result)
            nodes_visited.append(vector_operations_count)
            current_recall = len(set(knn_hits).intersection(set(script_hits)))
            recall_total += current_recall
            exact_total += len(script_hits)
            min_recall = min(min_recall, current_recall)

        return (
            {
                "avg_recall": recall_total / exact_total,
                "min_recall": min_recall,
                "k": k,
                "num_candidates": num_candidates,
                "avg_nodes_visited": statistics.mean(nodes_visited) if any([x > 0 for x in nodes_visited]) else None,
                "99th_percentile_nodes_visited": compute_percentile(nodes_visited, 99) if any([x > 0 for x in nodes_visited]) else None,
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

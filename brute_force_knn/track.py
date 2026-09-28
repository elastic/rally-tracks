import bz2
import json
import logging
import os
from typing import List

logger = logging.getLogger(__name__)

DEFAULT_K: int = 1000
SO_VECTOR_DIR = os.path.join(os.path.dirname(__file__), "..", "so_vector")
QUERIES_FILENAME = "queries.json.bz2"


def _load_queries() -> List:
    queries = []
    with bz2.open(os.path.join(SO_VECTOR_DIR, QUERIES_FILENAME), "r") as f:
        for line in f:
            queries.append(json.loads(line))
    return queries


class BruteForceSearchParamSource:
    """Param source for the dense_vector brute force KNN query."""

    def __init__(self, track, params, **kwargs):
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._index_name = params.get("index", default_index)
        self._params = params
        self._queries = _load_queries()
        self._iters = 0
        self._maxIters = len(self._queries)
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        query_vec = self._queries[self._iters]
        self._iters = (self._iters + 1) % self._maxIters
        k = self._params.get("k", DEFAULT_K)

        return {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "size": k,
            "body": {
                "query": {
                    "dense_vector": {
                        "field": "titleVector",
                        "query_vector": query_vec,
                        "similarity_function": "dot_product"
                    }
                },
                "_source": False,
                "fields": ["questionId"]
            },
        }


class BruteForceESQLParamSource:
    """Param source for the ESQL brute force KNN query."""

    def __init__(self, track, params, **kwargs):
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._index_name = params.get("index", default_index)
        self._params = params
        self._queries = _load_queries()
        self._iters = 0
        self._maxIters = len(self._queries)
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        query_vec = self._queries[self._iters]
        self._iters = (self._iters + 1) % self._maxIters
        k = self._params.get("k", DEFAULT_K)

        query = (
            f"FROM {self._index_name} METADATA _score "
            '| WHERE KNN(titleVector, ?query, {"similarity_function": "dot_product"}) '
            f"| SORT _score DESC | LIMIT {k} | KEEP questionId"
        )

        return {
            "query": query,
            "body": {"params": [{"query": query_vec}]},
        }


class KnnValidationParamSource:
    """Param source for KNN consistency validation between ESQL and dense_vector queries."""

    def __init__(self, track, params, **kwargs):
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._index_name = params.get("index", default_index)
        self._params = params
        self._queries = _load_queries()
        self.infinite = False

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        num_queries = self._params.get("num-validation-queries", 5)
        k = self._params.get("k", 10)
        return {
            "index": self._index_name,
            "k": k,
            "queries": self._queries[:num_queries],
        }


class KnnConsistencyValidator:
    """Runner that validates ESQL KNN and dense_vector KNN return the same document IDs."""

    async def __call__(self, es, params):
        index = params["index"]
        k = params.get("k", 10)
        queries = params["queries"]
        mismatches = []

        for i, query_vec in enumerate(queries):
            dense_result = await es.search(
                index=index,
                size=k,
                body={
                    "query": {
                        "dense_vector": {
                            "field": "titleVector",
                            "query_vector": query_vec,
                            "similarity_function": "dot_product",
                        }
                    }
                },
            )
            dense_hits = dense_result["hits"]["hits"]
            dense_ids = {hit["_id"] for hit in dense_hits}

            if len(dense_hits) != k:
                mismatches.append(f"query {i}: dense_vector returned {len(dense_hits)} hits, expected {k}")

            esql_query = (
                f"FROM {index} METADATA _id, _score "
                '| WHERE KNN(titleVector, ?query, {"similarity_function": "dot_product"}) '
                f"| SORT _score DESC | LIMIT {k}"
            )
            esql_result = await es.esql.query(
                body={"query": esql_query, "params": [{"query": query_vec}]},
            )
            columns = [col["name"] for col in esql_result["columns"]]
            id_idx = columns.index("_id")
            esql_ids = {row[id_idx] for row in esql_result["values"]}

            if len(esql_result["values"]) != k:
                mismatches.append(f"query {i}: ESQL returned {len(esql_result['values'])} hits, expected {k}")

            if dense_ids != esql_ids:
                only_dense = dense_ids - esql_ids
                only_esql = esql_ids - dense_ids
                mismatches.append(
                    f"query {i}: result mismatch — only in dense_vector: {only_dense}, only in ESQL: {only_esql}"
                )

        if mismatches:
            raise AssertionError("KNN consistency validation failed:\n" + "\n".join(mismatches))

        logger.info("KNN consistency validation passed for %d queries (k=%d)", len(queries), k)
        return {"weight": len(queries), "unit": "ops", "success": True}

    def __repr__(self):
        return "knn-consistency-validate"


def register(registry):
    registry.register_param_source("brute-force-dense-vector-param-source", BruteForceSearchParamSource)
    registry.register_param_source("brute-force-esql-knn-param-source", BruteForceESQLParamSource)
    registry.register_param_source("knn-validation-param-source", KnnValidationParamSource)
    registry.register_runner("knn-consistency-validate", KnnConsistencyValidator(), async_runner=True)

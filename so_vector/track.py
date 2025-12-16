import bz2
import json
import logging
import os
from typing import Any, Final, List, Optional

from esrally.driver import runner
from shared.runners.esql import EsqlProfileRunner

logger = logging.getLogger(__name__)
QUERIES_FILENAME: str = "queries.json.bz2"
TRUE_KNN_FILENAME: str = "queries-recall.json.bz2"
QUERIES_FILENAME_1K: str = "queries-1k.json.bz2"
TRUE_KNN_FILENAME_1K: str = "queries-recall-1k.json.bz2"

DEFAULT_K: Final[int] = 10


async def extract_exact_neighbors(query_vector: List[float], index: str, max_size: int, vector_field: str, filter, client) -> List[str]:
    if filter is None:
        raise ValueError("Filter must be provided for exact neighbors extraction.")
    script_query = {
        "query": {
            "script_score": {
                "query": filter,
                "script": {
                    "source": f"dotProduct(params.query, '{vector_field}') + 1.0",
                    "params": {"query": query_vector},
                },
            }
        },
        "_source": False,
        "docvalue_fields": ["questionId"],
    }
    script_result = await client.search(
        body=script_query,
        index=index,
        request_cache=True,
        size=max_size,
    )
    return [hit["fields"]["questionId"][0] for hit in script_result["hits"]["hits"]]


def compute_percentile(data: List[Any], percentile):
    size = len(data)
    if size <= 0:
        return None
    sorted_data = sorted(data)
    index = int(round(percentile * size / 100)) - 1
    return sorted_data[max(min(index, size - 1), 0)]


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
        with bz2.open(os.path.join(cwd, QUERIES_FILENAME), "r") as queries_file:
            for vector_query in queries_file:
                self._queries.append(json.loads(vector_query))
        self.infinite = True
        self._iters = 0
        self._maxIters = len(self._queries)

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        result = {"index": self._index_name, "cache": self._params.get("cache", False), "results-per-page": self._params.get("k", 10)}
        num_candidates: int | None = self._params.get("num_candidates", None)
        # if -1, then its unset. If set, just set it.
        oversample = self._params.get("oversample", -1)
        if oversample > -1 and self._exact_scan:
            raise ValueError("Oversampling is not supported for exact scan queries.")
        query_vec = self._queries[self._iters]
        self._iters += 1
        if self._iters >= self._maxIters:
            self._iters = 0

        if self._exact_scan:
            result["body"] = {
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "dotProduct(params.query, 'titleVector') + 1.0",
                            "params": {"query": query_vec},
                        },
                    }
                }
            }
            if "filter" in self._params:
                result["body"]["query"]["script_score"]["query"] = self._params["filter"]
        else:
            result["body"] = {
                "knn": {
                    "field": "titleVector",
                    "query_vector": query_vec,
                    "k": self._params.get("k", DEFAULT_K),
                    **({"num_candidates": num_candidates} if num_candidates is not None else {}),
                }
            }
            if "filter" in self._params:
                result["body"]["knn"]["filter"] = self._params["filter"]
            if oversample > -1:
                result["body"]["knn"]["rescore_vector"] = {"oversample": oversample}

        return result


class ESQLKnnParamSource(KnnParamSource):
    def params(self):
        # if -1, then its unset. If set, just set it.
        oversample = self._params.get("oversample", -1)
        if oversample > -1 and self._exact_scan:
            raise ValueError("Oversampling is not supported for exact scan queries.")

        k = self._params.get("k", DEFAULT_K)
        num_candidates: int | None = self._params.get("num_candidates", None)

        query_vec = self._queries[self._iters]
        self._iters += 1
        if self._iters >= self._maxIters:
            self._iters = 0

        if self._exact_scan:
            query = f"FROM {self._index_name} METADATA _id, _source"
            if "filter" in self._params:
                # Optionally append filter.
                query += " | where (" + self._params["filter"] + ")"
            query += (
                f"| EVAL score = V_DOT_PRODUCT(titleVector, {query_vec}) + 1.0 | KEEP _id, _source, score | SORT score desc | LIMIT {k}"
            )
        else:
            # Construct options JSON.
            options = []
            if num_candidates:
                options.append(f'"min_candidates":{num_candidates}')
            if oversample > -1:
                options.append(f'"rescore_oversample":{oversample}')
            options_param = "{" + ", ".join(options) + "}"

            query = f"FROM {self._index_name} METADATA _id, _score, _source | WHERE KNN(titleVector, {query_vec}, {options_param})"
            if "filter" in self._params:
                # Optionally append filter.
                query += " and (" + self._params["filter"] + ")"
            query += f"| KEEP _id, _score, _source | SORT _score desc | LIMIT {k}"

        return {"query": query}


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

    async def get_neighbors_for_query(self, index: str, query_id: int, size: int, filter, client) -> List[str]:
        # For now, we must calculate the exact neighbors, maybe we should cache this?
        # it would have to be cached per query and filter
        if filter is not None:
            query_vector = self._queries[query_id]
            extracted = await extract_exact_neighbors(
                query_vector=query_vector,
                index=index,
                max_size=size,
                vector_field="titleVector",
                filter=filter,
                client=client,
            )
            return extracted
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
        request_timeout = self._params.get("request-timeout", None)
        optional_params = {"request-timeout": request_timeout} if request_timeout else {}
        return {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "size": self._params.get("k", 10),
            "num_candidates": self._params.get("num_candidates", 50),
            "oversample": self._params.get("oversample", -1),
            "knn_vector_store": KnnVectorStore(),
            "filter": self._params.get("filter", None),
            **optional_params,
        }


# Used in tandem with the KnnRecallParamSource.
# reads the queries, executes knn search and compares the results with the true nearest neighbors
class KnnRecallRunner:
    def get_knn_query(self, query_vec, k, num_candidates, filter, oversample):
        knn = {
            "field": "titleVector",
            "query_vector": query_vec,
            "k": k,
            "num_candidates": num_candidates,
        }
        if oversample > -1:
            knn["rescore_vector"] = {"oversample": oversample}
        if filter is not None:
            knn["filter"] = filter
        return {"knn": knn, "_source": False, "docvalue_fields": ["questionId"]}

    async def __call__(self, es, params):
        k = params["size"]
        num_candidates = params["num_candidates"]
        index = params["index"]
        request_timeout = params.get("request-timeout", None)
        request_cache = params["cache"]
        filter = params["filter"]
        recall_total = 0
        exact_total = 0
        min_recall = k
        max_recall = 0

        if request_timeout:
            es = es.options(request_timeout=request_timeout)

        knn_vector_store: KnnVectorStore = params["knn_vector_store"]
        for query_id, query_vector in enumerate(knn_vector_store.get_query_vectors()):
            knn_body = self.get_knn_query(query_vector, k, num_candidates, filter, params["oversample"])
            knn_result = await es.search(
                body=knn_body,
                index=index,
                request_cache=request_cache,
                size=k,
            )
            knn_hits = [hit["fields"]["questionId"][0] for hit in knn_result["hits"]["hits"]]
            true_neighbors = await knn_vector_store.get_neighbors_for_query(index, query_id, k, filter, es)
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
            "oversample": params["oversample"],
            "is_filtered_search": filter is not None,
        }
        logger.info(f"Recall results: {to_return} for filter: {filter}")
        return to_return

    def __repr__(self, *args, **kwargs):
        return "knn-recall"


def register(registry):
    registry.register_param_source("knn-param-source", KnnParamSource)
    registry.register_param_source("esql-knn-param-source", ESQLKnnParamSource)
    registry.register_param_source("knn-recall-param-source", KnnRecallParamSource)
    registry.register_runner("knn-recall", KnnRecallRunner(), async_runner=True)
    registry.register_runner("esql-profile", EsqlProfileRunner(), async_runner=True)

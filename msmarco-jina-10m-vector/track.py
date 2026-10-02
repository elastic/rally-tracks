import bz2
import json
import logging
import os
import random
import statistics
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

QUERIES_FILENAME: str = "queries.json.bz2"
QUERIES_RECALL_FILENAME: str = "queries-recall-10k.json.bz2"


def extract_vector_operations_count(knn_result):
    vector_operations_count = 0
    profile = knn_result.get("profile")
    if profile is None:
        return vector_operations_count
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


def build_knn_query(
    query_vector,
    k: Optional[int] = None,
    num_candidates: Optional[int] = None,
    oversample_rescore: int = -1,
):
    knn_query = {"field": "emb", "query_vector": query_vector}
    if k is not None:
        knn_query["k"] = k
    if num_candidates is not None:
        knn_query["num_candidates"] = num_candidates
    if oversample_rescore >= 0:
        knn_query["rescore_vector"] = {"oversample": oversample_rescore}
    return knn_query


class KnnParamSource:
    def __init__(self, track, params, **kwargs):
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._index_name = params.get("index", default_index)
        self._params = params
        self._queries = []
        self._seed = params.get("seed")

        cwd = os.path.dirname(__file__)
        with bz2.open(os.path.join(cwd, QUERIES_FILENAME), "r") as queries_file:
            for vector_query in queries_file:
                self._queries.append(json.loads(vector_query))
        random.Random(self._seed).shuffle(self._queries)

        self._iters = 0
        self._max_iters = len(self._queries)
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        k = self._params.get("k")
        num_candidates = self._params.get("num-candidates")
        oversample_rescore = self._params.get("oversample-rescore", -1)

        query_vec = self._queries[self._iters]
        knn_query = build_knn_query(query_vec, k, num_candidates, oversample_rescore)

        result = {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "body": {"knn": knn_query},
        }
        if k is not None:
            result["size"] = k

        self._iters += 1
        if self._iters >= self._max_iters:
            self._iters = 0
        return result


class KnnRecallParamSource:
    def __init__(self, track, params, **kwargs):
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._index_name = params.get("index", default_index)
        self._params = params
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        return {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "k": self._params.get("k"),
            "num_candidates": self._params.get("num-candidates"),
            "oversample_rescore": self._params.get("oversample-rescore", -1),
        }


class KnnRecallRunner:
    async def __call__(self, es, params):
        k = params.get("k")
        num_candidates = params.get("num_candidates")
        index = params["index"]
        request_cache = params["cache"]
        recall_total = 0
        exact_total = 0
        min_recall = None
        nodes_visited = []
        effective_k = k

        cwd = os.path.dirname(__file__)
        with bz2.open(os.path.join(cwd, QUERIES_RECALL_FILENAME), "r") as queries_file:
            for line in queries_file:
                query = json.loads(line)
                knn_query = build_knn_query(query["emb"], k, num_candidates, params["oversample_rescore"])

                body = {
                    "knn": knn_query,
                    "_source": False,
                    "fields": ["docid"],
                    "profile": True,
                }
                search_kwargs = {"index": index, "request_cache": request_cache, "body": body}
                if k is not None:
                    search_kwargs["size"] = k
                knn_result = await es.search(**search_kwargs)
                knn_hits = [hit["fields"]["docid"][0] for hit in knn_result["hits"]["hits"]]

                query_effective_k = k if k is not None else len(knn_hits)
                if effective_k is None:
                    effective_k = query_effective_k

                recall_hits = []
                for i in range(min(query_effective_k, len(query["ids"]))):
                    doc_id, _score = query["ids"][i]
                    recall_hits.append(doc_id)

                nodes_visited.append(extract_vector_operations_count(knn_result))
                current_recall = len(set(knn_hits).intersection(set(recall_hits)))
                recall_total += current_recall
                exact_total += len(recall_hits)
                min_recall = current_recall if min_recall is None else min(min_recall, current_recall)

        if exact_total <= 0:
            return None

        result = {
            "avg_recall": recall_total / exact_total,
            "min_recall": min_recall,
            "effective_k": effective_k,
            "num_candidates": num_candidates,
            "avg_nodes_visited": statistics.mean(nodes_visited) if any(x > 0 for x in nodes_visited) else None,
            "99th_percentile_nodes_visited": compute_percentile(nodes_visited, 99) if any(x > 0 for x in nodes_visited) else None,
        }
        if k is not None:
            result["k"] = k
        logger.info(f"Recall results: {result}")
        return result

    def __repr__(self, *args, **kwargs):
        return "knn-recall"


def register(registry):
    registry.register_param_source("knn-param-source", KnnParamSource)
    registry.register_param_source("knn-recall-param-source", KnnRecallParamSource)
    registry.register_runner("knn-recall", KnnRecallRunner(), async_runner=True)

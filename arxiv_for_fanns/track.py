import functools
import json
import logging
import os
from collections import defaultdict

import zstandard
from esrally.track import loader

from .track_processor import ArxivQueriesDownloader

logger = logging.getLogger(__name__)

DEFAULT_QUERIES_FILENAME = "queries_emis.json.zst"
VECTOR_FIELD = "emb"


def _load_queries(queries_path):
    """Read all records from a zstd-compressed NDJSON file."""
    queries = []
    with zstandard.open(queries_path, "rt") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            queries.append(json.loads(line))
    return queries


class GroundTruthStore:
    """Cache for brute-force exact ground truth, keyed by (index, ingest_percentage, query_number).

    Uses an lru_cache singleton so the cache survives across sequential task steps in the same
    worker process. Do not cache anything loop-bound (async clients, locks) - only plain data.
    """

    def __init__(self):
        # (index, ingest_percentage) -> {query_number: [ordered docid strings]}
        self._store = defaultdict(dict)

    async def get(self, client, index, ingest_percentage, query_number, query, size, request_cache):
        cached = self._store[(index, ingest_percentage)].get(query_number)
        if cached is None or len(cached) < size:
            cached = await _exact_ground_truth(client, index, query, size, request_cache)
            self._store[(index, ingest_percentage)][query_number] = cached
        return cached[:size]

    @classmethod
    @functools.lru_cache(maxsize=1)
    def get_instance(cls):
        return cls()


async def _exact_ground_truth(client, index, query, k, request_cache):
    """Compute exact top-k ground truth via cosine similarity over the indexed subset.

    Returns an ordered list of docid strings (highest similarity first).
    """
    result = await client.search(
        index=index,
        body={
            "query": {
                "script_score": {
                    "query": query["filter"],
                    "script": {
                        "source": "cosineSimilarity(params.query, 'emb') + 1.0",
                        "params": {"query": query["emb"]},
                    },
                }
            },
            "size": k,
            "fields": ["docid"],
            "_source": False,
        },
        request_cache=request_cache,
    )
    ids = []
    for hit in result["hits"]["hits"]:
        docid_values = hit.get("fields", {}).get("docid")
        if docid_values is not None:
            ids.append(str(docid_values[0]))
    return ids


class KnnSearchParamSource:
    """Param source for the per-query standalone kNN search op.

    Cycles through a query list one entry per params() call so Rally measures
    one search per iteration and records real per-query service_time.
    """

    def __init__(self, track, params, **kwargs):
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._index_name = params.get("index", default_index)
        self._params = params

        queries_file = params.get("queries-file", DEFAULT_QUERIES_FILENAME)
        queries_path = os.path.join(os.path.dirname(__file__), queries_file)
        self._queries = _load_queries(queries_path)
        if not self._queries:
            raise ValueError(f"No queries loaded from '{queries_path}'. " "Ensure the track processor downloaded the queries file.")
        self._iters = 0
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        query = self._queries[self._iters]
        self._iters = (self._iters + 1) % len(self._queries)

        oversample = self._params.get("oversample")
        knn = {
            "field": VECTOR_FIELD,
            "query_vector": query["emb"],
            "k": self._params.get("k", 100),
            "num_candidates": self._params.get("num-candidates", 256),
            "filter": query["filter"],
        }
        if oversample is not None:
            knn["rescore_vector"] = {"oversample": oversample}
        return {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "body": {"knn": knn, "_source": False},
        }


class KnnRecallParamSource:
    def __init__(self, track, params, **kwargs):
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._index_name = params.get("index", default_index)
        self._params = params
        queries_file = params.get("queries-file", DEFAULT_QUERIES_FILENAME)
        self._queries_path = os.path.join(os.path.dirname(__file__), queries_file)
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        k = self._params.get("k", 100)
        return {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "k": k,
            "num_candidates": self._params.get("num-candidates", 256),
            "oversample": self._params.get("oversample"),
            "request-timeout": self._params.get("request-timeout", 600),
            "queries_path": self._queries_path,
            "ingest_percentage": self._params.get("ingest-percentage", 100),
            "ground_truth_k": self._params.get("ground-truth-k", k),
        }


class KnnRecallRunner:
    """Run a filtered kNN query for each entry in the queries file and compute recall."""

    async def __call__(self, es, params):
        k = params["k"]
        ground_truth_k = max(params.get("ground_truth_k", k), k)
        num_candidates = params["num_candidates"]
        index = params["index"]
        request_cache = params["cache"]
        request_timeout = params.get("request-timeout")
        queries_path = params["queries_path"]
        ingest_percentage = params.get("ingest_percentage", 100)

        if not os.path.isfile(queries_path):
            raise FileNotFoundError(
                f"Queries file not found at '{queries_path}'. " "The track processor should have downloaded it during track preparation."
            )

        client = es.options(request_timeout=request_timeout) if request_timeout else es
        oversample = params.get("oversample")
        store = GroundTruthStore.get_instance()

        recall_total = 0
        ground_truth_total = 0
        min_recall = None
        max_recall = None
        failed_queries = 0
        query_number = 0

        with zstandard.open(queries_path, "rt") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                query = json.loads(line)

                knn_clause = {
                    "field": VECTOR_FIELD,
                    "query_vector": query["emb"],
                    "k": k,
                    "num_candidates": num_candidates,
                    "filter": {"term": query.get("filter")},
                }
                if oversample is not None:
                    knn_clause["rescore_vector"] = {"oversample": oversample}

                try:
                    result = await client.search(
                        body={"knn": knn_clause, "fields": ["docid"], "_source": False},
                        index=index,
                        request_cache=request_cache,
                        size=k,
                    )
                except Exception:
                    logger.warning(
                        "Search failed for query with filter %s (k=%d, num_candidates=%d); skipping",
                        query.get("filter"),
                        k,
                        num_candidates,
                        exc_info=True,
                    )
                    failed_queries += 1
                    query_number += 1
                    continue

                knn_ids = set()
                for hit in result["hits"]["hits"]:
                    docid_values = hit.get("fields", {}).get("docid")
                    if docid_values is None:
                        continue
                    knn_ids.add(str(docid_values[0]))

                if ingest_percentage < 100:
                    ordered = await store.get(client, index, ingest_percentage, query_number, query, ground_truth_k, request_cache)
                    ground_truth = set(ordered[:k])
                else:
                    ground_truth = {str(doc_id) for doc_id in query["ids"][:k]}

                ground_truth_count = len(ground_truth)
                matched_count = len(knn_ids & ground_truth)
                current_recall = matched_count / ground_truth_count if ground_truth_count > 0 else None

                if current_recall is not None:
                    recall_total += matched_count
                    ground_truth_total += ground_truth_count
                    min_recall = current_recall if min_recall is None else min(min_recall, current_recall)
                    max_recall = current_recall if max_recall is None else max(max_recall, current_recall)

                query_number += 1

        avg_recall = recall_total / ground_truth_total if ground_truth_total > 0 else None

        result_dict = {
            "avg_recall": avg_recall,
            "min_recall": min_recall,
            "max_recall": max_recall,
            "k": k,
            "num_candidates": num_candidates,
            "failed_queries": failed_queries,
        }
        logger.info("knn-recall results: %r", result_dict)
        return result_dict

    def __repr__(self, *args, **kwargs):
        return "knn-recall"


def register(registry):
    registry.register_track_processor(ArxivQueriesDownloader())
    registry.register_track_processor(loader.DefaultTrackPreparator())
    registry.register_param_source("knn-search-param-source", KnnSearchParamSource)
    registry.register_param_source("knn-recall-param-source", KnnRecallParamSource)
    registry.register_runner("knn-recall", KnnRecallRunner(), async_runner=True)

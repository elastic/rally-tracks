import json
import logging
import os

import zstandard
from esrally.track import loader

from .track_processor import ArxivQueriesDownloader

logger = logging.getLogger(__name__)

QUERIES_FILENAME = "queries_emis.json.zst"
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


def _term_filter_to_esql(filter_dict):
    """Convert a single-field dict like {"main_categories": "gr-qc"} to an ESQL predicate."""
    if len(filter_dict) != 1:
        raise ValueError(f"Expected a single-field filter dict, got {filter_dict!r}")
    field, value = next(iter(filter_dict.items()))
    return f'{field} == "{value}"'


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

        queries_file = params.get("queries-file", QUERIES_FILENAME)
        queries_path = os.path.join(os.path.dirname(__file__), queries_file)
        self._queries = _load_queries(queries_path)
        if not self._queries:
            raise ValueError(
                f"No queries loaded from '{queries_path}'. "
                "Ensure the track processor downloaded the queries file."
            )
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
            "filter": {"term": query["filter"]},
        }
        if oversample is not None:
            knn["rescore_vector"] = {"oversample": oversample}
        return {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "body": {"knn": knn, "_source": False},
        }


class ESQLKnnParamSource:
    """Param source for ESQL KNN search, using the same per-query filter as KnnSearchParamSource."""

    def __init__(self, track, params, **kwargs):
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._index_name = params.get("index", default_index)
        self._params = params

        queries_file = params.get("queries-file", QUERIES_FILENAME)
        queries_path = os.path.join(os.path.dirname(__file__), queries_file)
        self._queries = _load_queries(queries_path)
        if not self._queries:
            raise ValueError(
                f"No queries loaded from '{queries_path}'. "
                "Ensure the track processor downloaded the queries file."
            )
        self._iters = 0
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        query = self._queries[self._iters]
        self._iters = (self._iters + 1) % len(self._queries)

        k = self._params.get("k", 100)
        num_candidates = self._params.get("num-candidates", 256)
        oversample = self._params.get("oversample")

        options = []
        if num_candidates:
            options.append(f'"min_candidates":{num_candidates}')
        if oversample is not None:
            options.append(f'"rescore_oversample":{oversample}')
        options_str = "{" + ", ".join(options) + "}"

        vector_str = json.dumps(query["emb"])
        esql_filter = _term_filter_to_esql(query["filter"])
        esql_query = (
            f"FROM `{self._index_name}` METADATA _id, _score"
            f" | WHERE KNN({VECTOR_FIELD}, {vector_str}, {options_str})"
            f" and ({esql_filter})"
            f" | KEEP _id, _score | SORT _score desc | LIMIT {k}"
        )
        return {
            "query": esql_query,
            "body": {},
        }


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
        queries_file = self._params.get("queries-file", QUERIES_FILENAME)
        queries_path = os.path.join(os.path.dirname(__file__), queries_file)
        return {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "k": self._params.get("k", 100),
            "num_candidates": self._params.get("num-candidates", 256),
            "oversample": self._params.get("oversample"),
            "request_timeout": self._params.get("request-timeout", 600),
            "queries_path": queries_path,
        }


class KnnRecallRunner:
    """Run a filtered kNN query for each entry in the queries file and compute recall."""

    async def __call__(self, es, params):
        k = params["k"]
        num_candidates = params["num_candidates"]
        index = params["index"]
        request_cache = params["cache"]
        request_timeout = params.get("request_timeout")
        queries_path = params["queries_path"]

        if not os.path.isfile(queries_path):
            raise FileNotFoundError(
                f"Queries file not found at '{queries_path}'. "
                "The track processor should have downloaded it during track preparation."
            )

        client = es.options(request_timeout=request_timeout) if request_timeout else es
        oversample = params.get("oversample")

        recall_total = 0
        ground_truth_total = 0
        min_recall = None
        max_recall = None
        failed_queries = 0

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
                    continue

                # Extract docid from each hit; skip hits where the field is absent.
                knn_ids = set()
                for hit in result["hits"]["hits"]:
                    docid_values = hit.get("fields", {}).get("docid")
                    if docid_values is None:
                        continue
                    knn_ids.add(str(docid_values[0]))

                ground_truth = {str(doc_id) for doc_id in query["ids"][:k]}
                ground_truth_count = len(ground_truth)
                matched_count = len(knn_ids & ground_truth)
                current_recall = matched_count / ground_truth_count if ground_truth_count > 0 else None

                if current_recall is not None:
                    recall_total += matched_count
                    ground_truth_total += ground_truth_count
                    min_recall = current_recall if min_recall is None else min(min_recall, current_recall)
                    max_recall = current_recall if max_recall is None else max(max_recall, current_recall)

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
    registry.register_param_source("esql-knn-param-source", ESQLKnnParamSource)
    registry.register_param_source("knn-recall-param-source", KnnRecallParamSource)
    registry.register_runner("knn-recall", KnnRecallRunner(), async_runner=True)

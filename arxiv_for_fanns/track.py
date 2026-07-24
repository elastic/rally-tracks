import json
import logging
import os

import zstandard
from esrally.track import loader

from .track_processor import ArxivQueriesDownloader

logger = logging.getLogger(__name__)

QUERIES_FILENAME = "queries_emis.json.zst"
VECTOR_FIELD = "emb"


def _load_queries_bounded(queries_path, max_queries):
    """Read up to max_queries records from a zstd-compressed NDJSON file.

    If max_queries <= 0, all records are loaded.
    """
    queries = []
    with zstandard.open(queries_path, "rt") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            queries.append(json.loads(line))
            if 0 < max_queries <= len(queries):
                break
    return queries


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
        max_queries = params.get("search-query-count", 10000)
        self._queries = _load_queries_bounded(queries_path, max_queries)
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

        knn = {
            "field": VECTOR_FIELD,
            "query_vector": query["emb"],
            "k": self._params.get("k", 10),
            "num_candidates": self._params.get("num-candidates", 100),
            "filter": {"term": query["filter"]},
        }
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
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        queries_file = self._params.get("queries-file", QUERIES_FILENAME)
        queries_path = os.path.join(os.path.dirname(__file__), queries_file)
        return {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "k": self._params.get("k", 10),
            "num_candidates": self._params.get("num-candidates", 100),
            "request_timeout": self._params.get("request-timeout", 600),
            "queries_path": queries_path,
            "debug_sample_size": self._params.get("debug-sample-size", 5),
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
        debug_sample_size = params.get("debug_sample_size", 5)

        logger.info(
            "knn-recall starting: index=%s k=%d num_candidates=%d request_timeout=%s "
            "queries_path=%s debug_sample_size=%d",
            index, k, num_candidates, request_timeout, queries_path, debug_sample_size,
        )

        if not os.path.isfile(queries_path):
            raise FileNotFoundError(
                f"Queries file not found at '{queries_path}'. "
                "The track processor should have downloaded it during track preparation."
            )

        client = es.options(request_timeout=request_timeout) if request_timeout else es

        recall_total = 0
        ground_truth_total = 0
        min_recall = k
        failed_queries = 0
        query_number = 0
        empty_result_warnings = 0
        missing_field_warnings = 0
        # Cap noisy anomaly warnings so a systematic problem does not flood the log.
        _WARN_CAP = 5

        with zstandard.open(queries_path, "rt") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                query = json.loads(line)
                query_filter = query.get("filter")
                raw_ids = query.get("ids", [])

                knn_clause = {
                    "field": VECTOR_FIELD,
                    "query_vector": query["emb"],
                    "k": k,
                    "num_candidates": num_candidates,
                    "filter": {"term": query_filter},
                }

                try:
                    result = await client.search(
                        body={"knn": knn_clause, "fields": ["docid"], "_source": False},
                        index=index,
                        request_cache=request_cache,
                        size=k,
                    )
                except Exception:
                    logger.warning(
                        "Search failed for query %d with filter %s (k=%d, num_candidates=%d); skipping",
                        query_number, query_filter, k, num_candidates,
                        exc_info=True,
                    )
                    failed_queries += 1
                    query_number += 1
                    continue

                hits = result["hits"]["hits"]
                total_hits = result["hits"].get("total", {})

                # Detailed per-query dump for the first debug_sample_size queries.
                if query_number < debug_sample_size:
                    id_sample = raw_ids[:10]
                    id_type = type(raw_ids[0]).__name__ if raw_ids else "n/a"
                    first_hit_fields = hits[0].get("fields") if hits else None
                    logger.info(
                        "knn-recall [query %d] filter=%r ids_count=%d ids_sample=%r id_type=%s "
                        "total_hits=%r returned_hits=%d first_hit_fields=%r",
                        query_number, query_filter, len(raw_ids), id_sample, id_type,
                        total_hits, len(hits), first_hit_fields,
                    )

                # Warn if the filter returned nothing (possible cause: filter matches no docs).
                if not hits:
                    if empty_result_warnings < _WARN_CAP:
                        logger.warning(
                            "knn-recall [query %d] zero hits returned for filter %r "
                            "(total_hits=%r). Possible causes: filter field value mismatch, "
                            "wrong field type, or no indexed docs with this category.",
                            query_number, query_filter, total_hits,
                        )
                        empty_result_warnings += 1

                # Extract docid from each hit; skip hits where the field is absent.
                knn_ids = set()
                for hit in hits:
                    docid_values = hit.get("fields", {}).get("docid")
                    if docid_values is None:
                        if missing_field_warnings < _WARN_CAP:
                            logger.warning(
                                "knn-recall [query %d] hit missing 'fields.docid': hit=%r",
                                query_number, {k_: hit[k_] for k_ in hit if k_ != "_source"},
                            )
                            missing_field_warnings += 1
                        continue
                    knn_ids.add(str(docid_values[0]))

                ground_truth = {str(doc_id) for doc_id in raw_ids[:k]}
                current_recall = len(knn_ids & ground_truth)

                # Per-query recall breakdown for the sample window.
                if query_number < debug_sample_size:
                    knn_sample = sorted(knn_ids)[:10]
                    gt_sample = sorted(ground_truth)[:10]
                    logger.info(
                        "knn-recall [query %d] knn_ids_sample=%r ground_truth_sample=%r "
                        "current_recall=%d (intersection of %d knn vs %d gt hits)",
                        query_number, knn_sample, gt_sample,
                        current_recall, len(knn_ids), len(ground_truth),
                    )

                recall_total += current_recall
                ground_truth_total += len(ground_truth)
                min_recall = min(min_recall, current_recall)
                query_number += 1

        avg_recall = recall_total / ground_truth_total if ground_truth_total > 0 else None

        result_dict = {
            "avg_recall": avg_recall,
            "min_recall": min_recall,
            "k": k,
            "num_candidates": num_candidates,
            "failed_queries": failed_queries,
        }
        logger.info("knn-recall results: %r", result_dict)

        if not avg_recall:
            logger.warning(
                "knn-recall avg_recall is %s after %d queries (%d failed). Likely causes: "
                "(1) id-space mismatch (ground-truth ids vs indexed docid field) -- check "
                "knn_ids_sample vs ground_truth_sample in the per-query logs above; "
                "(2) empty result sets due to filter mismatch (%d zero-hit queries logged); "
                "(3) docid field missing from hits (%d warnings); "
                "(4) ids list not sorted by similarity so ids[:k] is the wrong subset.",
                avg_recall, query_number, failed_queries,
                empty_result_warnings, missing_field_warnings,
            )

        return result_dict

    def __repr__(self, *args, **kwargs):
        return "knn-recall"


def register(registry):
    registry.register_track_processor(ArxivQueriesDownloader())
    registry.register_track_processor(loader.DefaultTrackPreparator())
    registry.register_param_source("knn-recall-param-source", KnnRecallParamSource)
    registry.register_param_source("knn-search-param-source", KnnSearchParamSource)
    registry.register_runner("knn-recall", KnnRecallRunner(), async_runner=True)

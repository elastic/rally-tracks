import json
import logging
import os
from typing import Any, Dict, List

import zstandard

from esrally.track import loader
from .track_processor import ArxivQueriesDownloader

logger = logging.getLogger(__name__)

QUERIES_FILENAME = "queries_emis.json.zst"
VECTOR_FIELD = "emb"


def _load_queries() -> List[Dict[str, Any]]:
    path = os.path.join(os.path.dirname(__file__), QUERIES_FILENAME)
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Queries file not found at '{path}'. "
            "The track processor should have downloaded it during track preparation."
        )
    queries = []
    with zstandard.open(path, "rt") as f:
        logger.debug("Reading queries from '%s'", path)
        for line in f:
            line = line.strip()
            if line:
                queries.append(json.loads(line))
    logger.debug("Loaded %d queries from '%s'", len(queries), path)
    return queries

class KnnRecallParamSource:
    def __init__(self, track, params, **kwargs):
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._index_name = params.get("index", default_index)
        self._params = params
        self._queries = _load_queries()
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        return {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "k": self._params.get("k", 10),
            "num_candidates": self._params.get("num-candidates", 100),
            "queries": self._queries,
        }


class KnnRecallRunner:
    """Run a filtered kNN query for each entry in queries.json and compute recall.
    """

    async def __call__(self, es, params):
        k = params["k"]
        num_candidates = params["num_candidates"]
        index = params["index"]
        request_cache = params["cache"]
        queries = params["queries"]

        recall_total = 0
        ground_truth_total = 0
        min_recall = k

        for query in queries:
            knn_clause = {
                "field": VECTOR_FIELD,
                "query_vector": query["emb"],
                "k": k,
                "num_candidates": num_candidates,
                "filter":  {"term": query.get("filter")},
            }

            result = await es.search(
                body={"knn": knn_clause, "fields": ["docid"], "_source": False},
                index=index,
                request_cache=request_cache,
                size=k,
            )

            knn_ids = {str(hit["fields"]["docid"][0]) for hit in result["hits"]["hits"]}
            ground_truth = {str(doc_id) for doc_id in query["ids"][:k]}

            current_recall = len(knn_ids & ground_truth)
            recall_total += current_recall
            ground_truth_total += len(ground_truth)
            min_recall = min(min_recall, current_recall)

        return (
            {
                "avg_recall": recall_total / ground_truth_total,
                "min_recall": min_recall,
                "k": k,
                "num_candidates": num_candidates,
            }
        )

    def __repr__(self, *args, **kwargs):
        return "knn-recall"


def register(registry):
    registry.register_track_processor(ArxivQueriesDownloader())
    registry.register_track_processor(loader.DefaultTrackPreparator())
    registry.register_param_source("knn-recall-param-source", KnnRecallParamSource)
    registry.register_runner("knn-recall", KnnRecallRunner(), async_runner=True)

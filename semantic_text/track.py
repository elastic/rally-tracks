import bz2
import csv
# import importlib.util
import json
import logging
import os
import statistics
from collections import defaultdict
from typing import Any, Dict, List

from esrally import paths
from esrally.driver import runner
from esrally.track import loader


# def _load_sibling_module(filename: str, module_alias: str):
#     """Load a .py file next to this one without relying on package-relative imports.
#
#     Rally's plugin loader doesn't register the track directory as a parent package
#     in sys.modules, and for tracks whose directory name is not a valid Python
#     identifier (e.g. containing hyphens) the namespace-package fallback also fails.
#     """
#     path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
#     spec = importlib.util.spec_from_file_location(module_alias, path)
#     module = importlib.util.module_from_spec(spec)
#     spec.loader.exec_module(module)
#     return module
#
#
# QueryAssetsDownloader = _load_sibling_module(
#     "track_processor.py", "wikipedia_bbq_disk_tuning_track_processor"
# ).QueryAssetsDownloader

logger = logging.getLogger(__name__)

Qrels = Dict[str, Dict[str, int]]
Results = Dict[str, Dict[str, float]]

SAMPLE_LOG_COUNT: int = 3  # Number of queries to log in detail


class QueryAssetsDownloader(loader.TrackProcessor):
    """
    For each corpus selected for the current race, downloads the query and
    qrels files that live alongside the corpus documents in object storage.
    Uses Rally's own Downloader, which supports https://, s3:// and gs:// base URLs.

    Reads the following challenge parameters:
      - corpora:         list of corpus names to prepare (required)
      - query_filename:  filename of the queries file in each corpus's base_url
      - qrels_filename:  filename of the qrels file in each corpus's base_url

    Files are written to <data_root_dir>/<corpus_name>/<filename>, matching Rally's
    convention for corpus data.

    Downloads are executed inline here rather than yielded as (func, params)
    tuples because Rally's plugin loader registers this module under a name
    containing hyphens (`wikipedia-bbq_disk-tuning.track`) that is not in
    sys.modules on worker actors — pickling any function defined here fails.
    """

    def __init__(self):
        self.cfg = None
        self.downloader = None

    def on_prepare_track(self, track, data_root_dir):
        ch_params = track.selected_challenge_or_default.parameters
        selected_corpora = set(ch_params.get("corpora") or [])
        filenames = [ch_params.get("query_filename"), ch_params.get("qrels_filename")]
        filenames = [f for f in filenames if f]

        logger.info(
            "Preparing query assets for selected corpora: %s, filenames: %s",
            selected_corpora, filenames,
        )

        for corpus in track.corpora:
            if corpus.name not in selected_corpora:
                continue
            if not corpus.documents:
                continue
            base_url = corpus.documents[0].base_url
            if not base_url:
                continue
            corpus_dir = os.path.join(data_root_dir, corpus.name)
            for filename in filenames:
                target_path = os.path.join(corpus_dir, filename)
                if os.path.isfile(target_path):
                    logger.info("Skipping download: [%s] already present.", target_path)
                    continue
                logger.info("Downloading: [%s] from [%s].", target_path, base_url)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                self.downloader.download(base_url=base_url, target_path=target_path, size_in_bytes=None)

        return []


def _corpus_data_dir(corpus_name: str) -> str:
    # Mirrors Rally's default `local.dataset.cache` setting
    # (see esrally/resources/rally.ini: `${CONFIG_DIR}/benchmarks/data`).
    # Respects the RALLY_HOME env var via `paths.rally_confdir()`.
    return os.path.join(paths.rally_confdir(), "benchmarks", "data", corpus_name)


def _resolve_asset_paths(track, params):
    """Resolve (queries_path, qrels_path) for the corpus being benchmarked.

    The corpus name is taken from either the operation's `corpus` param or the
    challenge-level `corpora` parameter. Filenames come from the challenge-level
    `query_filename` / `qrels_filename` parameters. Both must be populated by the
    track user via `--track-params`; they are resolved against the same location
    that `QueryAssetsDownloader` writes to during the prep phase.
    """
    ch_params = track.selected_challenge_or_default.parameters
    corpora = ch_params.get("corpora") or []
    corpus_name = params.get("corpus") or (corpora[0] if corpora else None)
    if not corpus_name:
        raise ValueError(
            "Cannot resolve query asset paths: no corpus selected. "
            "Set `--track-params=corpora=[\"<name>\"]` or pass `corpus` on the operation."
        )
    query_filename = ch_params.get("query_filename")
    qrels_filename = ch_params.get("qrels_filename")
    if not query_filename or not qrels_filename:
        raise ValueError(
            "Cannot resolve query asset paths: `query_filename` and `qrels_filename` "
            "challenge parameters must be set."
        )
    data_dir = _corpus_data_dir(corpus_name)
    return os.path.join(data_dir, query_filename), os.path.join(data_dir, qrels_filename)


def _format_ranked_list(ranked_items, relevant_docs):
    """Return a formatted string of ranked (doc_id, score) pairs annotated with qrel relevance."""
    lines = []
    for rank, (doc_id, score) in enumerate(ranked_items, start=1):
        rel = relevant_docs.get(doc_id, 0)
        rel_tag = f"  [rel={rel}]" if rel > 0 else ""
        lines.append(f"    {rank:>2}. {doc_id}  score={score:.4f}{rel_tag}")
    return "\n".join(lines) if lines else "    (empty)"


def _log_sample_query(query_idx, query_id, knn_doc_scores, bf_doc_scores, qrels, recall, bf_count):
    """Log a side-by-side ranking comparison for a single query against qrels."""
    relevant_docs = qrels.get(query_id, {})
    knn_ranked = sorted(knn_doc_scores.items(), key=lambda x: x[1], reverse=True)
    bf_ranked = sorted(bf_doc_scores.items(), key=lambda x: x[1], reverse=True)

    knn_list = _format_ranked_list(knn_ranked, relevant_docs)
    bf_list = _format_ranked_list(bf_ranked, relevant_docs)
    relevant_str = (
        ", ".join(f"{doc}(rel={score})" for doc, score in relevant_docs.items())
        or "(none in qrels)"
    )
    sep = "=" * 60

    logger.info(
        "\n%s\nSample query %d  query_id=%s\n"
        "Relevant docs : %s\n"
        "Recall vs brute force: %d / %d\n"
        "\nKNN results:\n%s\n"
        "\nBrute force results:\n%s\n%s",
        sep, query_idx + 1, query_id,
        relevant_str,
        recall, bf_count,
        knn_list,
        bf_list,
        sep,
    )


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


def calc_ndcg(qrels: Qrels, results: Results, k_list: list):
    import pytrec_eval as pe

    scores = defaultdict(float)

    metrics = ["ndcg_cut"]
    pytrec_strings = {f"{metric}.{','.join([str(k) for k in k_list])}" for metric in metrics}
    evaluator = pe.RelevanceEvaluator(qrels, pytrec_strings)
    pytrec_scores = evaluator.evaluate(results)

    for query_id in pytrec_scores.keys():
        for metric in metrics:
            for k in k_list:
                scores[f"{metric}@{k}"] += pytrec_scores[query_id][f"{metric}_{k}"]

    queries_count = len(pytrec_scores.keys())
    if queries_count == 0:
        return scores

    for metric in metrics:
        for k in k_list:
            scores[f"{metric}@{k}"] = float(scores[f"{metric}@{k}"] / queries_count)

    return scores


def calc_mrr(qrels: Qrels, results: Results) -> float:
    """
    Calculate Mean Reciprocal Rank (MRR) across all queries.

    MRR measures how high the first relevant document appears in the ranked
    result list. For each query, the reciprocal rank is 1/rank of the first
    relevant hit (1-indexed), or 0 if no relevant document appears in the
    results. MRR is the mean of these reciprocal ranks over all queries.

    Args:
        qrels: Relevance judgments mapping each query ID to a dict of
               {doc_id: relevance_score}. A document is considered relevant
               if its score is greater than 0. Typically contains only the
               most relevant document(s) per query.
               Example: {"q1": {"doc42": 1}, "q2": {"doc7": 2, "doc9": 1}}

        results: Top-K search results mapping each query ID to a dict of
                 {doc_id: retrieval_score}, where retrieval_score is the
                 similarity score returned by the search engine. Documents
                 are ranked in descending order of this score.
                 Example: {"q1": {"doc10": 0.95, "doc42": 0.88, "doc5": 0.72},
                           "q2": {"doc7": 0.91, "doc3": 0.85}}

    Returns:
        The MRR score as a float in [0, 1]. Returns 0.0 if results is empty.
    """
    if not results:
        return 0.0

    reciprocal_rank_sum = 0.0
    for query_id, doc_scores in results.items():
        # Sort retrieved documents by descending retrieval score to get the ranked list
        ranked_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        relevant_docs = qrels.get(query_id, {})
        for rank, (doc_id, _) in enumerate(ranked_docs, start=1):
            if relevant_docs.get(doc_id, 0) > 0:
                reciprocal_rank_sum += 1.0 / rank
                break  # Only the first relevant hit contributes to MRR

    return reciprocal_rank_sum / len(results)


def read_qrels(qrels_input_file):
    qrels = defaultdict(dict)
    with bz2.open(qrels_input_file, "rt") as input_file:
        tsv_reader = csv.reader(input_file, delimiter="\t")
        for row in tsv_reader:
            query_id, doc_id, score = row[0], row[1], row[2]
            qrels[query_id][doc_id] = int(score)

    return qrels


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

        queries_path, _ = _resolve_asset_paths(track, params)
        logger.info(f"Loading queries from {queries_path}")
        with bz2.open(queries_path, "r") as queries_file:
            for vector_query in queries_file:
                self._queries.append(json.loads(vector_query))
        self._iters = 0
        self._maxIters = len(self._queries)
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        top_k = self._params.get("k", 10)
        visit_percentage = self._params.get("visit-percentage")
        num_candidates = self._params.get("num-candidates", 50)
        query_vec = self._queries[self._iters]["embedding"]
        if visit_percentage is None:
            knn_query = {"field": "embedding", "query_vector": query_vec, "k": top_k, "num_candidates": num_candidates}
        else:
            knn_query = {"field": "embedding", "query_vector": query_vec, "k": top_k, "visit_percentage": visit_percentage}
        if self._params.get("oversample-rescore", -1) >= 0:
            knn_query["rescore_vector"] = {"oversample": self._params.get("oversample-rescore")}
        if "filter" in self._params:
            knn_query["filter"] = self._params["filter"]
        result = {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "size": top_k,
            "body": {"knn": knn_query},
        }

        self._iters += 1
        if self._iters >= self._maxIters:
            self._iters = 0
        return result


class KnnRecallParamSource:
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

        self._queries_path, self._qrels_path = _resolve_asset_paths(track, params)
        logger.info(f"Loading queries from {self._queries_path}")
        logger.info(f"Loading qrels from {self._qrels_path}")
        with bz2.open(self._queries_path, "r") as queries_file:
            for vector_query in queries_file:
                self._queries.append(json.loads(vector_query))
        self._iters = 0
        self._maxIters = len(self._queries)
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        return {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "size": self._params.get("k", 10),
            "num_candidates": self._params.get("num-candidates", 100),
            "visit_percentage": self._params.get("visit-percentage", -1),
            "oversample_rescore": self._params.get("oversample-rescore", -1),
            "queries_path": self._queries_path,
            "qrels_path": self._qrels_path,
        }


class KnnRecallRunner:
    async def __call__(self, es, params):
        top_k = params["size"]
        num_candidates = params["num_candidates"]
        visit_percentage = params["visit_percentage"]
        index = params["index"]
        request_cache = params["cache"]

        qrels = read_qrels(params["qrels_path"])
        knn_results = defaultdict(dict)
        brute_force_results = defaultdict(dict)
        recall_total = 0
        exact_total = 0
        min_recall = top_k
        nodes_visited = []
        query_idx = 0

        with bz2.open(params["queries_path"], "r") as queries_file:
            for line in queries_file:
                query = json.loads(line)
                query_id = query["query_id"]

                if visit_percentage is not None and visit_percentage > 0:
                    knn_query = {"field": "embedding", "query_vector": query["embedding"], "k": top_k, "visit_percentage": visit_percentage}
                else:
                    knn_query = {"field": "embedding", "query_vector": query["embedding"], "k": top_k, "num_candidates": num_candidates}
                if params["oversample_rescore"] >= 0:
                    knn_query["rescore_vector"] = {"oversample": params["oversample_rescore"]}
                body = {
                    "knn": knn_query,
                    "_source": False,
                    "fields": ["doc_id"],
                    "profile": True,
                }
                knn_result = await es.search(index=index, request_cache=request_cache, size=top_k, body=body)
                knn_hits = []
                for hit in knn_result["hits"]["hits"]:
                    doc_id = hit["fields"]["doc_id"][0]
                    if doc_id not in knn_results[query_id]:
                        knn_hits.append(doc_id)
                    knn_results[query_id][doc_id] = max(knn_results[query_id].get(doc_id, 0), hit["_score"])

                # Generate brute force results
                bf_body = {
                    "query": {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "lang": "painless",
                                "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                                "params": {"query_vector": query["embedding"]},
                            },
                        }
                    },
                    "_source": False,
                    "fields": ["doc_id"],
                }
                bf_result = await es.search(index=index, request_cache=request_cache, size=top_k, body=bf_body)
                brute_force_hits = []
                for hit in bf_result["hits"]["hits"]:
                    doc_id = hit["fields"]["doc_id"][0]
                    if doc_id not in brute_force_results[query_id]:
                        brute_force_hits.append(doc_id)
                    brute_force_results[query_id][doc_id] = max(brute_force_results[query_id].get(doc_id, 0), hit["_score"])

                vector_operations_count = extract_vector_operations_count(knn_result)
                nodes_visited.append(vector_operations_count)

                current_recall = len(set(knn_hits).intersection(set(brute_force_hits)))
                recall_total += current_recall
                exact_total += len(brute_force_hits)
                min_recall = min(min_recall, current_recall)

                if query_idx < SAMPLE_LOG_COUNT:
                    _log_sample_query(
                        query_idx,
                        query_id,
                        knn_doc_scores=dict(knn_results[query_id]),
                        bf_doc_scores=dict(brute_force_results[query_id]),
                        qrels=qrels,
                        recall=current_recall,
                        bf_count=len(brute_force_hits),
                    )
                query_idx += 1

        knn_ndcg = calc_ndcg(qrels, knn_results, [top_k])
        brute_force_ndcg = calc_ndcg(qrels, brute_force_results, [top_k])
        knn_mrr = calc_mrr(qrels, knn_results)
        brute_force_mrr = calc_mrr(qrels, brute_force_results)

        if exact_total == 0:
            logger.warning("No brute-force hits found; cannot compute recall or NDCG.")
            return None

        result = {
            f"bruteforce_ndcg_{top_k}": brute_force_ndcg[f"ndcg_cut@{top_k}"],
            f"knn_ndcg_{top_k}": knn_ndcg[f"ndcg_cut@{top_k}"],
            "bruteforce_mrr": brute_force_mrr,
            "knn_mrr": knn_mrr,
            "avg_recall": recall_total / exact_total,
            "min_recall": min_recall,
            "k": top_k,
            "num_candidates": num_candidates,
            "oversample_rescore": params["oversample_rescore"],
            "visit_percentage": visit_percentage,
            "avg_nodes_visited": statistics.mean(nodes_visited) if any(x > 0 for x in nodes_visited) else None,
            "99th_percentile_nodes_visited": compute_percentile(nodes_visited, 99) if any(x > 0 for x in nodes_visited) else None,
        }
        logger.info(
            "\nRecall summary over %d queries:\n"
            "  avg_recall                    : %.4f\n"
            "  min_recall                    : %d\n"
            "  knn_ndcg@%d                   : %.4f\n"
            "  bruteforce_ndcg@%d            : %.4f\n"
            "  knn_mrr                       : %.4f\n"
            "  bruteforce_mrr                : %.4f\n"
            "  avg_nodes_visited             : %s\n"
            "  99th_percentile_nodes_visited : %s\n"
            "  k=%d  num_candidates=%s  oversample_rescore=%s visit_percentage=%s",
            query_idx,
            result["avg_recall"],
            result["min_recall"],
            top_k, result[f"knn_ndcg_{top_k}"],
            top_k, result[f"bruteforce_ndcg_{top_k}"],
            knn_mrr,
            brute_force_mrr,
            result["avg_nodes_visited"],
            result["99th_percentile_nodes_visited"],
            top_k, num_candidates, params["oversample_rescore"], visit_percentage,
        )
        return result

    def __repr__(self, *args, **kwargs):
        return "knn-recall"

def register(registry):
    registry.register_param_source("knn-param-source", KnnParamSource)
    registry.register_param_source("knn-recall-param-source", KnnRecallParamSource)
    registry.register_runner("knn-recall", KnnRecallRunner(), async_runner=True)

    registry.register_track_processor(QueryAssetsDownloader())
    # Re-register the default preparator since declaring our own processor disables it.
    registry.register_track_processor(loader.DefaultTrackPreparator())

import csv
import json
import os
from collections import defaultdict
from typing import Dict

Qrels = Dict[str, Dict[str, int]]
Results = Dict[str, Dict[str, float]]


def calc_ndcg(qrels: Qrels, results: Results, k_list: list):
    import pytrec_eval as pe

    for qid, rels in results.items():
        for pid in list(rels):
            if qid == pid:
                results[qid].pop(pid)

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


def read_qrels(qrels_input_file):
    qrels = defaultdict(dict)
    with open(qrels_input_file, "r") as input_file:
        tsv_reader = csv.reader(input_file, delimiter="\t")
        for query_id, doc_id, score in tsv_reader:
            qrels[query_id][doc_id] = int(score)
    return qrels


def generate_weighted_terms_query(text_expansion_field, query_expansion, boost=1.0):
    return {
        "query": {
            "bool": {
                "should": [
                    {"term": {f"{text_expansion_field}": {"value": f"{key}", "boost": value}}} for key, value in query_expansion.items()
                ],
                "boost": boost,
            }
        }
    }


def generate_bm25_query(text_field, query, boost=1.0):
    return {"query": {"match": {f"{text_field}": {"query": query, "boost": boost}}}}


def generate_combine_bm25_weighted_terms_query(
    text_field, text_expansion_field, query, query_boost, query_expansion, query_expansion_boost
):
    """Legacy hybrid using bool/should. Works on all 8.x versions (pre-8.14 backward compat)."""
    return {
        "query": {
            "bool": {
                "should": [
                    generate_bm25_query(text_field, query, query_boost)["query"],
                    generate_weighted_terms_query(text_expansion_field, query_expansion, query_expansion_boost)["query"],
                ]
            }
        }
    }


def generate_rrf_hybrid_query(
    text_field,
    text_expansion_field,
    query,
    query_boost,
    query_expansion,
    query_expansion_boost,
    rank_window_size,
    rank_constant,
):
    """RRF retriever combining BM25 + weighted terms. Requires ES 8.14+."""
    bm25_retriever = {"standard": {"query": generate_bm25_query(text_field, query, query_boost)["query"]}}

    weighted_terms_retriever = {
        "standard": {"query": generate_weighted_terms_query(text_expansion_field, query_expansion, query_expansion_boost)["query"]}
    }

    return {
        "retriever": {
            "rrf": {
                "retrievers": [
                    bm25_retriever,
                    weighted_terms_retriever,
                ],
                "rank_window_size": rank_window_size,
                "rank_constant": rank_constant,
            }
        }
    }


def generate_linear_hybrid_query(
    text_field,
    text_expansion_field,
    query,
    query_boost,
    query_expansion,
    query_expansion_boost,
    rank_window_size,
    normalizer,
):
    """Linear retriever combining BM25 + weighted terms with score normalization. Requires ES 8.18+."""
    bm25_standard = {"standard": {"query": generate_bm25_query(text_field, query, 1)["query"]}}

    weighted_terms_standard = {"standard": {"query": generate_weighted_terms_query(text_expansion_field, query_expansion, 1)["query"]}}

    return {
        "retriever": {
            "linear": {
                "retrievers": [
                    {
                        "retriever": bm25_standard,
                        "weight": query_boost,
                        "normalizer": normalizer,
                    },
                    {
                        "retriever": weighted_terms_standard,
                        "weight": query_expansion_boost,
                        "normalizer": normalizer,
                    },
                ],
                "rank_window_size": rank_window_size,
            }
        }
    }


def generate_pruned_query(field, query_expansion, boost=1.0):
    return {"query": {"sparse_vector": {"field": field, "query_vector": query_expansion, "prune": True, "boost": boost}}}


def generate_rescored_pruned_query(field, query_expansion, num_candidates, boost=1.0):
    return {
        "query": {"sparse_vector": {"field": field, "query_vector": query_expansion, "prune": True, "boost": boost}},
        "rescore": {
            "window_size": num_candidates,
            "query": {
                "rescore_query": {
                    "sparse_vector": {
                        "field": field,
                        "query_vector": query_expansion,
                        "prune": True,
                        "pruning_config": {
                            "only_score_pruned_tokens": True,
                        },
                        "boost": boost,
                    }
                }
            },
        },
    }


class QueryParamsSource:
    def __init__(self, track, params, **kwargs):
        # choose a suitable index: if there is only one defined for this track
        # choose that one, but let the user always override index
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._index_name = params.get("index", default_index)
        self._cache = params.get("cache", False)
        self._size = params.get("size", 10)
        self._num_candidates = params.get("num_candidates", 10)
        self._text_field = params.get("text_field", "text")
        self._text_expansion_field = params.get("text_expansion_field", "text_expansion_elser")
        self._query_file = params.get("query_source", "queries.json")
        self._query_strategy = params.get("query_strategy", "bm25")
        self._track_total_hits = params.get("track_total_hits", False)
        self._rescore = params.get("rescore", False)
        self._prune = params.get("prune", False)
        self._params = params
        self.infinite = True

        cwd = os.path.dirname(__file__)
        with open(os.path.join(cwd, self._query_file), "r") as file:
            self._queries = json.load(file)
        self._iters = 0

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        query_obj = self._queries[self._iters]
        if self._query_strategy == "bm25":
            query = generate_bm25_query(text_field=self._text_field, query=query_obj["query"], boost=1)
        elif self._query_strategy == "text_expansion":
            if self._prune is False:
                query = generate_weighted_terms_query(
                    text_expansion_field=self._text_expansion_field, query_expansion=query_obj[self._text_expansion_field], boost=1
                )
            elif self._rescore is True:
                query = generate_rescored_pruned_query(
                    field=self._text_expansion_field,
                    query_expansion=query_obj[self._text_expansion_field],
                    num_candidates=self._num_candidates,
                    boost=1,
                )
            else:
                query = generate_pruned_query(
                    field=self._text_expansion_field, query_expansion=query_obj[self._text_expansion_field], boost=1
                )
        elif self._query_strategy == "hybrid":
            query = generate_combine_bm25_weighted_terms_query(
                self._text_field,
                self._text_expansion_field,
                query_obj["query"],
                1,
                query_obj[self._text_expansion_field],
                1,
            )
        elif self._query_strategy == "rrf":
            query = generate_rrf_hybrid_query(
                self._text_field,
                self._text_expansion_field,
                query_obj["query"],
                1,
                query_obj[self._text_expansion_field],
                1,
                rank_window_size=self._params.get("rank_window_size", 10),
                rank_constant=self._params.get("rank_constant", 60),
            )
        elif self._query_strategy == "linear":
            query = generate_linear_hybrid_query(
                self._text_field,
                self._text_expansion_field,
                query_obj["query"],
                self._params.get("query_boost", 1),
                query_obj[self._text_expansion_field],
                self._params.get("query_expansion_boost", 1),
                rank_window_size=self._params.get("rank_window_size", 10),
                normalizer=self._params.get("normalizer", "minmax"),
            )
        else:
            raise Exception(
                f"The query strategy `{self._query_strategy}` is not implemented. "
                f"Supported strategies: bm25, text_expansion, hybrid, rrf, linear"
            )

        self._iters = (self._iters + 1) % len(self._queries)
        query["track_total_hits"] = self._track_total_hits
        query["size"] = self._size
        return {
            "index": self._index_name,
            "cache": self._cache,
            "body": query,
        }


class WeightedRecallParamSource:
    def __init__(self, track, params, **kwargs):
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._query_file = params.get("query_source", "queries-small.json")
        self._qrels_file = params.get("qrels_source", "qrels-small.tsv")
        self._index_name = params.get("index", default_index)
        self._cache = params.get("cache", False)
        self._top_k = params.get("top_k", 10)
        self._num_candidates = params.get("num_candidates", 100)
        self._params = params
        self._queries = []
        self._text_expansion_field = params.get("text_expansion_field", "text_expansion_elser")
        self.infinite = True

        cwd = os.path.dirname(__file__)
        with open(os.path.join(cwd, self._query_file), "r") as file:
            self._queries = json.load(file)
        self._qrels = read_qrels(os.path.join(cwd, self._qrels_file))

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        return {
            "index": self._index_name,
            "cache": self._cache,
            "top_k": self._top_k,
            "num_candidates": self._num_candidates,
            "queries": self._queries,
            "qrels": self._qrels,
            "text_expansion_field": self._text_expansion_field,
        }


# For each query this will generate the weighted terms query, a pruned version and a rescored pruned version of the same query.
# These queries can then be executed and compared for accuracy.
class WeightedTermsRecallRunner:
    async def __call__(self, es, params):
        recall_total = 0
        recall_with_rescore_total = 0
        exact_total = 0
        min_recall = params["top_k"]
        weighted_term_results = defaultdict(dict)
        pruned_results = defaultdict(dict)
        pruned_rescored_results = defaultdict(dict)

        for query in params["queries"]:
            query_id = query["id"]

            # Build and execute all three queries
            weighted_terms_result = await es.search(
                body=generate_weighted_terms_query(params["text_expansion_field"], query[params["text_expansion_field"]], 1),
                index=params["index"],
                request_cache=params["cache"],
                size=params["top_k"],
            )
            pruned_result = await es.search(
                body=generate_pruned_query(params["text_expansion_field"], query[params["text_expansion_field"]], 1),
                index=params["index"],
                request_cache=params["cache"],
                size=params["top_k"],
            )
            pruned_rescored_result = await es.search(
                body=generate_rescored_pruned_query(
                    params["text_expansion_field"], query[params["text_expansion_field"]], params["num_candidates"], 1
                ),
                index=params["index"],
                request_cache=params["cache"],
                size=params["top_k"],
            )

            weighted_terms_hits = {hit["_source"]["id"]: hit["_score"] for hit in weighted_terms_result["hits"]["hits"]}
            pruned_hits = {hit["_source"]["id"]: hit["_score"] for hit in pruned_result["hits"]["hits"]}
            pruned_rescored_hits = {hit["_source"]["id"]: hit["_score"] for hit in pruned_rescored_result["hits"]["hits"]}

            # Recall calculations as compared to the control/non-pruned hits
            weighted_terms_ids = set(weighted_terms_hits.keys())
            pruned_ids = set(pruned_hits.keys())
            pruned_rescored_ids = set(pruned_rescored_hits.keys())
            current_recall_with_rescore = len(weighted_terms_ids.intersection(pruned_rescored_ids))
            current_recall = len(weighted_terms_ids.intersection(pruned_ids))
            recall_with_rescore_total += current_recall_with_rescore
            recall_total += current_recall
            exact_total += len(weighted_terms_ids)
            min_recall = min(min_recall, current_recall)

            # Construct input to NDCG calculation based on returned hits
            for doc_id, score in weighted_terms_hits.items():
                weighted_term_results[query_id][doc_id] = score
            for doc_id, score in pruned_hits.items():
                pruned_results[query_id][doc_id] = score
            for doc_id, score in pruned_rescored_hits.items():
                pruned_rescored_results[query_id][doc_id] = score

        control_relevance = calc_ndcg(params["qrels"], weighted_term_results, [10, 100])
        pruned_relevance = calc_ndcg(params["qrels"], pruned_results, [10, 100])
        pruned_rescored_relevance = calc_ndcg(params["qrels"], pruned_rescored_results, [10, 100])

        return (
            {
                "avg_recall": float(recall_with_rescore_total / exact_total),  # Calculated on pruned/rescored hits
                "avg_recall_without_rescore": float(recall_total / exact_total),  # Calculated on pruned hits without rescore
                "min_recall": min_recall,  # Calculated on pruned/rescored hits
                "top_k": params["top_k"],
                "num_candidates": params["num_candidates"],
                "control_ndcg_10": control_relevance["ndcg_cut@10"],
                "control_ndcg_100": control_relevance["ndcg_cut@100"],
                "pruned_ndcg_10": pruned_relevance["ndcg_cut@10"],
                "pruned_ndcg_100": pruned_relevance["ndcg_cut@100"],
                "pruned_rescored_ndcg_10": pruned_rescored_relevance["ndcg_cut@10"],
                "pruned_rescored_ndcg_100": pruned_rescored_relevance["ndcg_cut@100"],
            }
            if exact_total > 0
            else None
        )

    def __repr__(self, *args, **kwargs):
        return "weighted_terms_recall"


def register(registry):
    registry.register_param_source("query_param_source", QueryParamsSource)
    registry.register_param_source("weighted_terms_recall_param_source", WeightedRecallParamSource)
    registry.register_runner("weighted_terms_recall", WeightedTermsRecallRunner(), async_runner=True)

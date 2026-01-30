import bz2
import csv
import json
import logging
import os
import statistics
from collections import defaultdict
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

Qrels = Dict[str, Dict[str, int]]
Results = Dict[str, Dict[str, float]]

QUERIES_FILENAME: str = "queries.json.bz2"
QUERIES_RECALL_FILENAME: str = "queries-recall.json.bz2"


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


def read_qrels(qrels_input_file):
    qrels = defaultdict(dict)
    with open(qrels_input_file, "r") as input_file:
        tsv_reader = csv.reader(input_file, delimiter="\t")
        for query_id, doc_id, score, _ in tsv_reader:
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

        cwd = os.path.dirname(__file__)
        with bz2.open(os.path.join(cwd, QUERIES_FILENAME), "r") as queries_file:
            for vector_query in queries_file:
                self._queries.append(json.loads(vector_query))
        self._iters = 0
        self._maxIters = len(self._queries)
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        top_k = self._params.get("k", 10)
        num_candidates = self._params.get("num-candidates", 50)
        query_vec = self._queries[self._iters]
        knn_query = {"field": "emb", "query_vector": query_vec, "k": top_k, "num_candidates": num_candidates}
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
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._index_name = params.get("index", default_index)
        self._cache = params.get("cache", False)
        self._params = params
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        return {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "size": self._params.get("k", 10),
            "num_candidates": self._params.get("num-candidates", 100),
            "oversample_rescore": self._params.get("oversample-rescore", -1),
        }


class KnnRecallRunner:
    async def __call__(self, es, params):
        top_k = params["size"]
        num_candidates = params["num_candidates"]
        index = params["index"]
        request_cache = params["cache"]

        cwd = os.path.dirname(__file__)
        qrels = read_qrels(os.path.join(cwd, "qrels.tsv"))
        results = defaultdict(dict)
        best_results = defaultdict(dict)
        recall_total = 0
        exact_total = 0
        min_recall = top_k
        nodes_visited = []
        with bz2.open(os.path.join(cwd, QUERIES_RECALL_FILENAME), "r") as queries_file:
            for line in queries_file:
                query = json.loads(line)
                query_id = query["query_id"]

                knn_query = {"field": "emb", "query_vector": query["emb"], "k": top_k, "num_candidates": num_candidates}
                if params["oversample_rescore"] >= 0:
                    knn_query["rescore_vector"] = {"oversample": params["oversample_rescore"]}
                body = {
                    "knn": knn_query,
                    "_source": False,
                    "fields": ["docid"],
                    "profile": True,
                }
                knn_result = await es.search(index=index, request_cache=request_cache, size=top_k, body=body)
                knn_hits = []
                for hit in knn_result["hits"]["hits"]:
                    doc_id = hit["fields"]["docid"][0]
                    results[query_id][doc_id] = hit["_score"]
                    knn_hits.append(doc_id)
                recall_hits = []
                for i in range(top_k):
                    doc_id, score = query["ids"][i]
                    recall_hits.append(doc_id)
                    best_results[query_id][doc_id] = score
                vector_operations_count = extract_vector_operations_count(knn_result)
                nodes_visited.append(vector_operations_count)
                current_recall = len(set(knn_hits).intersection(set(recall_hits)))
                recall_total += current_recall
                exact_total += len(recall_hits)
                min_recall = min(min_recall, current_recall)
        relevance_res = calc_ndcg(qrels, results, [top_k])
        best_relevance_res = calc_ndcg(qrels, best_results, [top_k])
        result = (
            {
                f"best_ndcg_{top_k}": best_relevance_res[f"ndcg_cut@{top_k}"],
                f"ndcg_{top_k}": relevance_res[f"ndcg_cut@{top_k}"],
                "avg_recall": recall_total / exact_total,
                "min_recall": min_recall,
                "k": top_k,
                "num_candidates": num_candidates,
                "avg_nodes_visited": statistics.mean(nodes_visited) if any([x > 0 for x in nodes_visited]) else None,
                "99th_percentile_nodes_visited": compute_percentile(nodes_visited, 99) if any([x > 0 for x in nodes_visited]) else None,
            }
            if exact_total > 0
            else None
        )
        logger.info(f"Recall results: {result}")
        return result

    def __repr__(self, *args, **kwargs):
        return "knn-recall"


def register(registry):
    registry.register_param_source("knn-param-source", KnnParamSource)
    registry.register_param_source("knn-recall-param-source", KnnRecallParamSource)
    registry.register_runner("knn-recall", KnnRecallRunner(), async_runner=True)

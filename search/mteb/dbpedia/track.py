import csv
import json
import logging
import os
from collections import defaultdict
from typing import Dict

Qrels = Dict[str, Dict[str, int]]
Results = Dict[str, Dict[str, float]]

logger = logging.getLogger(__name__)


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
        next(tsv_reader)  # Skip column names
        for query_id, doc_id, score in tsv_reader:
            qrels[query_id][doc_id] = int(score)
    return qrels


def generate_bm25_query(text_field, query, boost=1.0):
    return {"query": {"match": {f"{text_field}": {"query": query, "boost": boost}}}}


def generate_query(query_string, title_field, title_boost, text_field, text_boost):
    return {
        "query": {
            "multi_match": {
                "minimum_should_match": "1<-1 3<49%",
                "type": "best_fields",
                "fuzziness": "AUTO",
                "prefix_length": 2,
                "query": query_string,
                "fields": [f"{title_field}^{title_boost}", f"{text_field}^{text_boost}"],
            }
        }
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
        self._title_field = params.get("title_field", "title")
        self._text_field = params.get("text_field", "text")
        self._title_boost = params.get("title_boost", 5)
        self._text_boost = params.get("text_boost", 1)
        self._query_file = params.get("query_source", "queries.json")
        self._track_total_hits = params.get("track_total_hits", False)
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
        query = generate_query(query_obj["text"], self._title_field, self._title_boost, self._text_field, self._text_boost)
        query["track_total_hits"] = self._track_total_hits
        query["size"] = self._size

        self._iters = (self._iters + 1) % len(self._queries)
        return {
            "index": self._index_name,
            "cache": self._cache,
            "body": query,
        }


class RelevanceParamsSource:
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
        self._title_field = params.get("title_field", "title")
        self._text_field = params.get("text_field", "text")
        self._title_boost = params.get("title_boost", 5)
        self._text_boost = params.get("text_boost", 1)
        self._query_file = params.get("query_source", "queries.json")
        self._qrels_file = params.get("qrels_source", "test.tsv")
        self._params = params
        self.infinite = True

        cwd = os.path.dirname(__file__)
        with open(os.path.join(cwd, self._query_file), "r") as file:
            self._queries = json.load(file)
        self._iters = 0

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
            "size": self._size,
            "queries": self._queries,
            "qrels": self._qrels,
            "text_field": self._text_field,
            "title_field": self._title_field,
            "text_boost": self._text_boost,
            "title_boost": self._title_boost,
        }


class TextSearchRelevanceRunner:
    async def __call__(self, es, params):
        text_search_results = defaultdict(dict)

        for query in params["queries"]:
            query_id = query["_id"]

            text_search_query = generate_query(
                query["text"], params["title_field"], params["title_boost"], params["text_field"], params["text_boost"]
            )
            text_search_result = await es.search(
                body=text_search_query,
                index=params["index"],
                request_cache=params["cache"],
                size=params["size"],
            )

            text_search_hits = {hit["_source"]["id"]: hit["_score"] for hit in text_search_result["hits"]["hits"]}

            # Construct input to NDCG calculation based on returned hits
            for doc_id, score in text_search_hits.items():
                text_search_results[query_id][doc_id] = score

        text_search_relevance = calc_ndcg(params["qrels"], text_search_results, [10, 100])

        logger.debug(
            f'text_search_relevance_10 = {text_search_relevance["ndcg_cut@10"]}, text_search_relevance_100 = {text_search_relevance["ndcg_cut@100"]}'
        )

        return {
            "text_search_relevance_10": text_search_relevance["ndcg_cut@10"],
            "text_search_relevance_100": text_search_relevance["ndcg_cut@100"],
        }

    def __repr__(self, *args, **kwargs):
        return "text_search_relevance"


def register(registry):
    registry.register_param_source("query_param_source", QueryParamsSource)
    registry.register_param_source("relevance_param_source", RelevanceParamsSource)
    registry.register_runner("text_search_relevance", TextSearchRelevanceRunner(), async_runner=True)

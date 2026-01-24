import bz2
import json
import os

QUERIES_FILENAME: str = "queries-recall.json.bz2"

class HybridParamSource:
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

        query = self._queries[self._iters]
        self._iters += 1
        if self._iters >= self._maxIters:
            self._iters = 0

        knn_query = {"field": "emb", "query_vector": query["emb"], "k": top_k, "num_candidates": num_candidates}
        if self._params.get("oversample-rescore", -1) >= 0:
            knn_query["rescore_vector"] = {"oversample": self._params.get("oversample-rescore")}
        if "filter" in self._params:
            knn_query["filter"] = self._params["filter"]

        knn_retriever = {
            "knn": knn_query
        }

        # standard_retriever = {
        #     "standard": {
        #         "query": {
        #             "combined_fields": {
        #                 "query": query["text"],
        #                 "fields": ["title", "text"]
        #             }
        #         }
        #     }
        # }
        standard_retriever = {
            "standard": {
                "query": {
                    "match": {
                        "text": query["text"]
                    }
                }
            }
        }

        return {
            "method": "POST",
            "path": f"/{self._index_name}/_search",
            "body": {
                "_source": False,
                "retriever": {
                    "rrf": {
                        "retrievers": [
                            standard_retriever,
                            knn_retriever
                        ]
                    }
                },
                "size": self._size
            }
        }

class EsqlHybridParamSource:
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

        query = self._queries[self._iters]
        self._iters += 1
        if self._iters >= self._maxIters:
            self._iters = 0

        options = []
        options.append(f'"min_candidates":{num_candidates}')
        if self._params.get("oversample-rescore", -1) >= 0:
            options.append(f'"rescore_oversample":{self._params.get("oversample-rescore")}')
        knn_options = "{" + ", ".join(options) + "}"
        knn_query = f"WHERE KNN(emb, ?query_vector, {knn_options})"

        if "filter" in self._params:
            knn_query += " and (" + self._params["filter"] + ")"

        lexical_query = f"WHERE MATCH(text, ?query_text)"

        hybrid_query = f"FROM {self._index_name} METADATA _index, _id, _score"
        hybrid_query += f" | FORK ({lexical_query} | DROP emb) ({knn_query} | DROP emb) | FUSE | KEEP _index, _id, _score | LIMIT {self._size}"

        query_vector = query["emb"]
        query_text = query["text"]
        params = [{"query_vector": query_vector}, {"query_text": query_text}]
        return {"query": hybrid_query, "body": {"params": params }}


def register(registry):
    registry.register_param_source("hybrid-bm25-knn-param-source", HybridParamSource)
    registry.register_param_source("esql-hybrid-bm25-knn-param-source", EsqlHybridParamSource)

import random

from esrally.track.params import ParamSource


class RandomBulkParamSource(ParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self._bulk_size = params.get("bulk-size", 1000)
        self._index_name = params.get("index", track.indices[0].name)
        self._dims = params.get("dims", 128)
        self._partitions = params.get("partitions", 1000)
        self._routing = params.get("routing", False)

    def params(self):
        import numpy as np

        bulk_data = []
        for _ in range(self._bulk_size):
            vec = np.random.rand(self._dims)
            partition_id = random.randint(0, self._partitions)
            metadata = {"_index": self._index_name}
            if self._routing:
                metadata["routing"] = partition_id
            bulk_data.append({"index": metadata})
            bulk_data.append({"partition_id": partition_id, "emb": vec.tolist()})

        return {
            "body": bulk_data,
            "bulk-size": self._bulk_size,
            "action-metadata-present": True,
            "unit": "docs",
            "index": self._index_name,
            "type": "",
        }


def generate_knn_query(query_vector, partition_id, k):
    return {
        "knn": {
            "field": "emb",
            "query_vector": query_vector,
            "k": k,
            "num_candidates": k,
            "filter": {"term": {"partition_id": partition_id}},
        }
    }


def generate_script_query(query_vector, partition_id):
    return {
        "query": {
            "script_score": {
                "query": {"term": {"partition_id": partition_id}},
                "script": {"source": "cosineSimilarity(params.query_vector, 'emb') + 1.0", "params": {"query_vector": query_vector}},
            }
        }
    }


class RandomSearchParamSource:
    def __init__(self, track, params, **kwargs):
        # choose a suitable index: if there is only one defined for this track
        # choose that one, but let the user always override index
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._index_name = params.get("index", default_index)
        self._cache = params.get("cache", False)
        self._partitions = params.get("partitions", 1000)
        self._dims = params.get("dims", 128)
        self._top_k = params.get("k", 10)
        self._script = params.get("script", True)
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        import numpy as np

        partition_id = random.randint(0, self._partitions)
        query_vec = np.random.rand(self._dims).tolist()
        if self._script:
            query = generate_script_query(query_vec, partition_id)
        else:
            query = generate_knn_query(query_vec, partition_id, self._topk)
        return {"index": self._index_name, "cache": self._cache, "size": self._top_k, "_source_excludes": ["emb"], "body": query}


def register(registry):
    registry.register_param_source("random-bulk-param-source", RandomBulkParamSource)
    registry.register_param_source("knn-param-source", RandomSearchParamSource)

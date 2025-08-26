import random
import time

from esrally.track.params import ParamSource


class RandomBulkParamSource(ParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self._bulk_size = params.get("bulk-size", 1000)
        self._index_name = track.data_streams[0].name
        self._dims = params.get("dims", 128)
        self._partitions = params.get("partitions", 1000)
        self._paragraph_size = params.get("paragraph-size", 1)

    def params(self):
        import numpy as np

        timestamp = int(time.time()) * 1000
        bulk_data = []
        for _ in range(self._bulk_size):
            partition_id = random.randint(0, self._partitions)
            metadata = {"_index": self._index_name}
            bulk_data.append({"create": metadata})
            doc = {"@timestamp": timestamp, "partition_id": partition_id}
            if self._paragraph_size > 1:
                nested_vec = []
                for i in range(0, self._paragraph_size):
                    nested_vec.append({"emb": np.random.rand(self._dims).tolist(), "paragraph_id": i})
                doc["nested"] = nested_vec
            else:
                doc["emb"] = np.random.rand(self._dims).tolist()
            bulk_data.append(doc)

        return {
            "body": bulk_data,
            "bulk-size": self._bulk_size,
            "action-metadata-present": True,
            "unit": "docs",
            "index": self._index_name,
            "type": "",
        }


def generate_knn_query(field_name, query_vector, partition_id, k, rescore_oversample):
    return {
        "knn": {
            "field": field_name,
            "query_vector": query_vector,
            "k": k,
            "num_candidates": k,
            "filter": {"term": {"partition_id": partition_id}},
            "rescore_vector": {"oversample": rescore_oversample},
        },
    }


class RandomSearchParamSource:
    def __init__(self, track, params, **kwargs):
        self._index_name = track.data_streams[0].name
        self._cache = params.get("cache", False)
        self._field = params.get("field", "emb")
        self._partitions = params.get("partitions", 1000)
        self._dims = params.get("dims", 128)
        self._top_k = params.get("k", 10)
        self._rescore_oversample = params.get("rescore-oversample", 0)
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        import numpy as np

        partition_id = random.randint(0, self._partitions)
        query_vec = np.random.rand(self._dims).tolist()
        query = generate_knn_query(self._field, query_vec, partition_id, self._top_k, self._rescore_oversample)
        return {"index": self._index_name, "cache": self._cache, "size": self._top_k, "body": query}


def register(registry):
    registry.register_param_source("random-bulk-param-source", RandomBulkParamSource)
    registry.register_param_source("knn-param-source", RandomSearchParamSource)

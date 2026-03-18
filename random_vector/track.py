from bisect import bisect_left
import random
import time

from esrally.track.params import ParamSource

TIER_SMALL = "small"
TIER_MEDIUM = "medium"
TIER_LARGE = "large"
TIERS = (TIER_SMALL, TIER_MEDIUM, TIER_LARGE)

# Size ranges per tier (document counts)
TIER_RANGES = {
    TIER_SMALL: (1000, 10000),
    TIER_MEDIUM: (10000, 100000),
    TIER_LARGE: (100000, 1000000),
}


def build_partition_registry(small_partitions, medium_partitions, large_partitions, partition_seed):
    """
    Build a deterministic partition registry from the given counts and seed.
    Returns a list of (partition_id, target_size, tier) tuples and a list of
    cumulative weights for weighted random selection during indexing.
    """
    rng = random.Random(partition_seed)
    partitions = []
    cumulative_weights = []
    cumulative_weight = 0
    partition_id = 0
    for tier, count in [(TIER_SMALL, small_partitions), (TIER_MEDIUM, medium_partitions), (TIER_LARGE, large_partitions)]:
        lo, hi = TIER_RANGES[tier]
        for _ in range(count):
            target_size = rng.randint(lo, hi)
            partitions.append((str(partition_id), target_size, tier))
            cumulative_weight += target_size
            cumulative_weights.append(cumulative_weight)
            partition_id += 1

    if not partitions:
        raise ValueError("At least one partition must be configured")

    return partitions, cumulative_weights


def extract_partition_config(params):
    small = params.get("small-partitions", 100)
    medium = params.get("medium-partitions", 20)
    large = params.get("large-partitions", 5)
    seed = params.get("partition-seed", 42)

    for name, value in (("small-partitions", small), ("medium-partitions", medium), ("large-partitions", large)):
        if value < 0:
            raise ValueError(f"{name} must be non-negative")

    if small + medium + large == 0:
        raise ValueError("At least one partition must be configured")

    return small, medium, large, seed


def pick_partition(partitions, cumulative_weights):
    """Select a partition using weighted random sampling (proportional to target size)."""
    partition_index = bisect_left(cumulative_weights, random.randint(1, cumulative_weights[-1]))
    return partitions[partition_index]


class RandomBulkParamSource(ParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self._bulk_size = params.get("bulk-size", 1000)
        self._index_name = track.data_streams[0].name
        self._dims = params.get("dims", 128)
        self._paragraph_size = params.get("paragraph-size", 1)

        small, medium, large, seed = extract_partition_config(params)
        self._partitions, self._cumulative = build_partition_registry(small, medium, large, seed)

    def params(self):
        import numpy as np

        timestamp = int(time.time()) * 1000
        bulk_data = []
        for _ in range(self._bulk_size):
            partition_id, _, _ = pick_partition(self._partitions, self._cumulative)
            metadata = {"_index": self._index_name, "routing": partition_id}
            bulk_data.append({"create": metadata})
            doc = {"@timestamp": timestamp, "partition_id": partition_id}
            if self._paragraph_size > 1:
                nested_vec = []
                for i in range(self._paragraph_size):
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
    knn_query = {
        "field": field_name,
        "query_vector": query_vector,
        "k": k,
        "num_candidates": k,
        "filter": {"term": {"partition_id": partition_id}},
    }

    if rescore_oversample > 0:
        knn_query["rescore_vector"] = {"oversample": rescore_oversample}

    return {"knn": knn_query}


class RandomSearchParamSource:
    def __init__(self, track, params, **kwargs):
        self._index_name = track.data_streams[0].name
        self._cache = params.get("cache", False)
        self._field = params.get("field", "emb")
        self._dims = params.get("dims", 128)
        self._top_k = params.get("k", 10)
        self._rescore_oversample = params.get("rescore-oversample", 0)

        small, medium, large, seed = extract_partition_config(params)
        self._partitions, _ = build_partition_registry(small, medium, large, seed)

        partition_tier = params.get("partition-tier", None)
        if partition_tier is not None:
            if partition_tier not in TIERS:
                raise ValueError(f"partition-tier must be one of: {', '.join(TIERS)}")
            self._tier_partitions = [p for p in self._partitions if p[2] == partition_tier]
        else:
            self._tier_partitions = self._partitions

        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        import numpy as np

        partition = random.choice(self._tier_partitions)
        partition_id = partition[0]
        query_vec = np.random.rand(self._dims).tolist()
        query = generate_knn_query(self._field, query_vec, partition_id, self._top_k, self._rescore_oversample)
        return {"index": self._index_name, "cache": self._cache, "size": self._top_k, "body": query}


def register(registry):
    registry.register_param_source("random-bulk-param-source", RandomBulkParamSource)
    registry.register_param_source("knn-param-source", RandomSearchParamSource)

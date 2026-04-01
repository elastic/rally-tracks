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


class PartitionRegistry:
    """Lightweight partition registry that derives partition IDs on the fly.

    Instead of materializing a list of every partition, this stores only
    per-tier counts and uses two-level selection (pick tier, then pick
    index within tier).  Memory usage is O(num_tiers) regardless of how
    many partitions are configured.
    """

    def __init__(self, small_partitions, medium_partitions, large_partitions):
        self._rng = random.Random()
        tier_counts = [
            (TIER_SMALL, small_partitions),
            (TIER_MEDIUM, medium_partitions),
            (TIER_LARGE, large_partitions),
        ]

        # For weighted indexing: weight each tier by count * midpoint(range)
        # so larger-tier partitions receive proportionally more documents.
        self._weighted_tiers = []
        self._weighted_cumulative = []
        cum = 0.0
        for tier, count in tier_counts:
            if count > 0:
                lo, hi = TIER_RANGES[tier]
                cum += count * (lo + hi) / 2
                self._weighted_tiers.append((tier, count))
                self._weighted_cumulative.append(cum)

        # For uniform search: weight each tier by its partition count
        # so every partition is equally likely to be queried.
        self._uniform_tiers = []
        self._uniform_cumulative = []
        cum_count = 0
        for tier, count in tier_counts:
            if count > 0:
                cum_count += count
                self._uniform_tiers.append((tier, count))
                self._uniform_cumulative.append(cum_count)

        if not self._weighted_tiers:
            raise ValueError("At least one partition must be configured")

    def pick_weighted(self):
        """Select a partition weighted by expected tier size (for indexing)."""
        return self._pick(self._rng, self._weighted_tiers, self._weighted_cumulative)

    def pick_uniform(self):
        """Select a partition uniformly at random (for search)."""
        return self._pick(self._rng, self._uniform_tiers, self._uniform_cumulative)

    @staticmethod
    def _pick(rng, tiers, cumulative):
        r = rng.random() * cumulative[-1]
        for cum_w, (tier, count) in zip(cumulative, tiers):
            if r < cum_w:
                return f"{tier}-{rng.randrange(count)}"
        # Fallback for floating-point edge case (r == cumulative[-1])
        tier, count = tiers[-1]
        return f"{tier}-{rng.randrange(count)}"


def extract_partition_config(params):
    small = params.get("small-partitions", 100)
    medium = params.get("medium-partitions", 20)
    large = params.get("large-partitions", 5)

    for name, value in (("small-partitions", small), ("medium-partitions", medium), ("large-partitions", large)):
        if value < 0:
            raise ValueError(f"{name} must be non-negative")

    if small + medium + large == 0:
        raise ValueError("At least one partition must be configured")

    return small, medium, large


class RandomBulkParamSource(ParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self._bulk_size = params.get("bulk-size", 1000)
        self._index_name = track.data_streams[0].name
        self._dims = params.get("dims", 128)
        self._paragraph_size = params.get("paragraph-size", 1)
        self._custom_routing = params.get("custom-routing", False)

        small, medium, large = extract_partition_config(params)
        self._registry = PartitionRegistry(small, medium, large)

    def params(self):
        import numpy as np

        timestamp = int(time.time()) * 1000
        bulk_data = []
        for _ in range(self._bulk_size):
            partition_id = self._registry.pick_weighted()
            metadata = {"_index": self._index_name}
            if self._custom_routing:
                metadata["routing"] = partition_id
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

    if rescore_oversample >= 0:
        knn_query["rescore_vector"] = {"oversample": rescore_oversample}

    return {"knn": knn_query}


class RandomSearchParamSource:
    def __init__(self, track, params, **kwargs):
        self._index_name = track.data_streams[0].name
        self._cache = params.get("cache", False)
        self._field = params.get("field", "emb")
        self._dims = params.get("dims", 128)
        self._top_k = params.get("k", 10)
        self._rescore_oversample = params.get("rescore-oversample", -1)

        partition_tier = params.get("partition-tier", None)
        if partition_tier is not None:
            if partition_tier not in TIERS:
                raise ValueError(f"partition-tier must be one of: {', '.join(TIERS)}")
            count = params.get(f"{partition_tier}-partitions")
            if count is None or count <= 0:
                raise ValueError(f"{partition_tier}-partitions must be positive when partition-tier is set")
            self._partition_tier = partition_tier
            self._tier_partition_count = count
            self._registry = None
        else:
            small, medium, large = extract_partition_config(params)
            self._registry = PartitionRegistry(small, medium, large)
            self._partition_tier = None

        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        import numpy as np

        if self._partition_tier is not None:
            partition_id = f"{self._partition_tier}-{random.randrange(self._tier_partition_count)}"
        else:
            partition_id = self._registry.pick_uniform()
        query_vec = np.random.rand(self._dims).tolist()
        query = generate_knn_query(self._field, query_vec, partition_id, self._top_k, self._rescore_oversample)
        return {"index": self._index_name, "cache": self._cache, "size": self._top_k, "body": query}


class KnnRecallParamSource:
    def __init__(self, track, params, **kwargs):
        self._index_name = track.data_streams[0].name
        self._field = params.get("field", "emb")
        self._dims = params.get("dims", 128)
        self._top_k = params.get("k", 10)
        self._rescore_oversample = params.get("rescore-oversample", -1)
        self._recall_iterations = params.get("recall-iterations", 100)

        partition_tier = params.get("partition-tier")
        if partition_tier not in TIERS:
            raise ValueError(f"partition-tier must be one of: {', '.join(TIERS)}")
        count = params.get(f"{partition_tier}-partitions")
        if count is None or count <= 0:
            raise ValueError(f"{partition_tier}-partitions must be positive when partition-tier is set")
        self._partition_tier = partition_tier
        self._tier_partition_count = count
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        import numpy as np

        query_vectors = [np.random.rand(self._dims).tolist() for _ in range(self._recall_iterations)]
        partition_ids = [
            f"{self._partition_tier}-{random.randrange(self._tier_partition_count)}"
            for _ in range(self._recall_iterations)
        ]
        return {
            "index": self._index_name,
            "field": self._field,
            "k": self._top_k,
            "rescore_oversample": self._rescore_oversample,
            "query_vectors": query_vectors,
            "partition_ids": partition_ids,
        }


class KnnRecallRunner:
    async def __call__(self, es, params):
        k = params["k"]
        index = params["index"]
        field = params["field"]
        rescore_oversample = params["rescore_oversample"]
        query_vectors = params["query_vectors"]
        partition_ids = params["partition_ids"]

        recall_total = 0
        exact_total = 0
        min_recall = k
        max_recall = 0

        for query_vec, partition_id in zip(query_vectors, partition_ids):
            knn_body = generate_knn_query(field, query_vec, partition_id, k, rescore_oversample)
            knn_body["_source"] = False
            knn_result = await es.search(body=knn_body, index=index, size=k)
            knn_hits = [hit["_id"] for hit in knn_result["hits"]["hits"]]

            exact_body = {
                "query": {
                    "script_score": {
                        "query": {"term": {"partition_id": partition_id}},
                        "script": {
                            "source": f"cosineSimilarity(params.query, '{field}') + 1.0",
                            "params": {"query": query_vec},
                        },
                    }
                },
                "_source": False,
            }
            exact_result = await es.search(body=exact_body, index=index, size=k)
            exact_hits = [hit["_id"] for hit in exact_result["hits"]["hits"]]

            current_recall = len(set(knn_hits).intersection(set(exact_hits)))
            recall_total += current_recall
            exact_total += len(exact_hits)
            min_recall = min(min_recall, current_recall)
            max_recall = max(max_recall, current_recall)

        return (
            {
                "avg_recall": recall_total / exact_total,
                "min_recall": min_recall,
                "max_recall": max_recall,
                "k": k,
            }
            if exact_total > 0
            else None
        )

    def __repr__(self, *args, **kwargs):
        return "knn-recall"


def register(registry):
    registry.register_param_source("random-bulk-param-source", RandomBulkParamSource)
    registry.register_param_source("knn-param-source", RandomSearchParamSource)
    registry.register_param_source("knn-recall-param-source", KnnRecallParamSource)
    registry.register_runner("knn-recall", KnnRecallRunner(), async_runner=True)

import functools
import json
import logging
import os
import re

from collections import defaultdict
from esrally.track import loader
from esrally.track.track import Task, Parallel
logger = logging.getLogger(__name__)


def load_query_vectors(queries_file):
    if not (os.path.exists(queries_file) and os.path.isfile(queries_file)):
        raise ValueError(f"Provided queries file %s does not exist or is not a file" % queries_file)
    query_vectors: dict[str, list[float]]
    with open(queries_file, 'r') as f:
        logger.info(f"Reading query vectors from '{queries_file}'")
        lines = f.readlines()
        query_vectors = {_index: json.loads(vector) for _index, vector in enumerate(lines)}
        logger.info(f"Finished reading query vectors from '{queries_file}'")
    return query_vectors


async def extract_exact_neighbors(query_vector: list[float], index: str, max_size: int, client) -> list[str]:
    script_query = await client.search(
        body={
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query, 'vector') + 1.0",
                        "params": {"query": query_vector},
                    },
                }
            },
            "_source": False,
        },
        index=index,
        size=max_size,
    )
    return [hit["_id"] for hit in script_query["hits"]["hits"]]


class KnnVectorStore:

    def __init__(self, queries_file: str):
        self._query_vectors = load_query_vectors(queries_file)
        self._store = defaultdict(lambda: defaultdict(list))

    async def get_neighbors_for_query(self, index: str, query_id: str, max_size: int, client) -> list[str]:
        try:
            logger.debug(f"Fetching exact neighbors for {query_id} from in-memory store")
            if not (index in self._store and query_id in self._store[index]):
                logger.debug(f"Query vector with id {query_id} not cached - computing neighbors")
                self._store[index][query_id] = await self.load_exact_neighbors(index, query_id, max_size, client)
                logger.debug(f"Finished computing exact neighbors for {query_id} - it's now cached!")
            return self._store[index][query_id]
        except Exception as ex:
            return []

    async def load_exact_neighbors(self, index: str, query_id: str, max_size: int, client):
        if query_id not in self._query_vectors:
            raise ValueError(f"Unknown query with id: '{query_id}' provided")
        return await extract_exact_neighbors(self._query_vectors[query_id], index, max_size, client)

    def get_query_vectors(self) -> dict[str, list[float]]:
        return self._query_vectors

    @classmethod
    @functools.lru_cache(maxsize=1)
    def get_instance(cls, queries_file: str):
        logger.info(f"Initializing KnnVectorStore for queries file: '{queries_file}'")
        return KnnVectorStore(queries_file)


class KnnRecallProcessor:

    KNN_RECALL_OPERATION_PATTERN = re.compile(r"knn-recall-(\d+)-(\d+)")

    def on_after_load_track(self, t):
        max_k = 0
        tasks_to_update = []
        for challenge in t.challenges:
            for task in challenge.schedule:
                if isinstance(task, Task):
                    task_matched = self.KNN_RECALL_OPERATION_PATTERN.search(task.operation.name)
                    if task_matched:
                        tasks_to_update.append(task)
                        matched_k_parameter = task_matched.group(1)
                        max_k = max(max_k, int(matched_k_parameter))
                elif isinstance(task, Parallel):
                    for nested_task in task.tasks:
                        task_matched = self.KNN_RECALL_OPERATION_PATTERN.search(nested_task.operation.name)
                        if task_matched:
                            tasks_to_update.append(nested_task)
                            matched_k_parameter = task_matched.group(1)
                            max_k = max(max_k, int(matched_k_parameter))
            for task in tasks_to_update:
                task.operation.params.update({"max_k": max_k})

    def on_prepare_track(self, track, data_root_dir):
        return []

    def __repr__(self, *args, **kwargs):
        return "knn-recall-processor"


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
        self._exact_scan = params.get("exact", False)
        self._params = params
        self._queries = []

        cwd = os.path.dirname(__file__)
        with open(os.path.join(cwd, "queries.json"), "r") as file:
            for line in file:
                self._queries.append(json.loads(line))
        self._iters = 0
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        result = {"index": self._index_name, "cache": self._params.get("cache", False), "size": self._params.get("k", 10)}

        if self._exact_scan:
            result["body"] = {
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query, 'vector') + 1.0",
                            "params": {"query": self._queries[self._iters]},
                        },
                    }
                },
                "_source": False,
            }
        else:
            result["body"] = {
                "knn": {
                    "field": "vector",
                    "query_vector": self._queries[self._iters],
                    "k": self._params.get("k", 10),
                    "num_candidates": self._params.get("num-candidates", 100),
                },
                "_source": False,
            }
        self._iters += 1
        if self._iters >= len(self._queries):
            self._iters = 0
        return result


# For each query this will generate both the knn query and the equivalent
# score script query. The two queries can then be executed and used
# to gauge the accuracy of the knn query.
class KnnRecallParamSource:
    def __init__(self, track, params, **kwargs):
        if len(track.indices) == 1:
            default_index = track.indices[0].name
        else:
            default_index = "_all"

        self._index_name = params.get("index", default_index)
        self._cache = params.get("cache", False)
        self._params = params
        self._queries = []
        self.infinite = True
        cwd = os.path.dirname(__file__)
        self._queries_file = os.path.join(cwd, "queries.json")

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        return {
            "index": self._index_name,
            "cache": self._params.get("cache", False),
            "size": self._params.get("k", 10),
            "num_candidates": self._params.get("num-candidates", 100),
            "queries_file": self._queries_file,
            "max_k": self._params.get("max_k", 42)
        }


# Used in tandem with the KnnRecallParamSource. This executes both a knn query
# and an equivalent score script query. Results are then compared to gauge
# the accuracy of the knn query.
class KnnRecallRunner:
    async def __call__(self, es, params):
        k = params["size"]
        num_candidates = params["num_candidates"]
        index = params["index"]
        request_cache = params["cache"]
        queries_file = params["queries_file"]
        max_k = max(params["max_k"], k)
        recall_total = 0
        exact_total = 0
        min_recall = k

        knn_vector_store: KnnVectorStore = KnnVectorStore.get_instance(queries_file)
        for query_id, query_vector in knn_vector_store.get_query_vectors().items():
            knn_result = await es.search(
                body={
                    "knn": {
                        "field": "vector",
                        "query_vector": query_vector,
                        "k": k,
                        "num_candidates": num_candidates,
                    },
                    "_source": False,
                },
                index=index,
                request_cache=request_cache,
                size=k,
            )
            knn_hits = [hit["_id"] for hit in knn_result["hits"]["hits"]]
            script_hits = await knn_vector_store.get_neighbors_for_query(index, query_id, max_k, es)
            script_hits = script_hits[:k]
            current_recall = len(set(knn_hits).intersection(set(script_hits)))
            recall_total += current_recall
            exact_total += len(script_hits)
            min_recall = min(min_recall, current_recall)

        return (
            {
                "avg_recall": recall_total / exact_total,
                "min_recall": min_recall,
                "k": k,
                "num_candidates": num_candidates,
            }
            if exact_total > 0
            else None
        )

    def __repr__(self, *args, **kwargs):
        return "knn-recall"


def register(registry):
    registry.register_param_source("knn-param-source", KnnParamSource)
    registry.register_param_source("knn-recall-param-source", KnnRecallParamSource)
    registry.register_runner("knn-recall", KnnRecallRunner(), async_runner=True)
    registry.register_track_processor(KnnRecallProcessor())
    # TODO change this based on https://github.com/elastic/rally/issues/1257
    try:
        registry.register_track_processor(loader.DefaultTrackPreparator())
    except TypeError as e:
        if e == "__init__() missing 1 required positional argument: 'cfg'":
            pass

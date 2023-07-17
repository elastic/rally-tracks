import csv
import random
from os import getcwd
from os.path import dirname
from typing import Iterator

from esrally.track.params import ParamSource

QUERIES_DIRNAME: str = dirname(f"{getcwd()}/{__file__}")
QUERIES_FILENAME: str = f"{QUERIES_DIRNAME}/queries.csv"

SEARCH_APPLICATION_ROOT_ENDPOINT: str = "/_application/search_application/"


def query_iterator(k: int) -> Iterator[str]:
    with open(QUERIES_FILENAME) as queries_file:
        csv_reader = csv.reader(queries_file)
        next(csv_reader)
        queries_with_probabilities = list(tuple(line) for line in csv_reader)

        queries = [query for query, _ in queries_with_probabilities]
        probabilities = [float(probability) for _, probability in queries_with_probabilities]

        for query in random.choices(queries, weights=probabilities, k=k):
            yield query


class CreateSearchApplicationParamSource(ParamSource):
    def __init__(self, track, params, **kwargs):
        print(track)
        super().__init__(track, params, **kwargs)

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        return {
            "method": "PUT",
            "path": f"{SEARCH_APPLICATION_ROOT_ENDPOINT}wikipedia",
            "body": {"indices": ["wikipedia"]},
        }


def register(registry):
    registry.register_param_source("create-search-application-param-source", CreateSearchApplicationParamSource)

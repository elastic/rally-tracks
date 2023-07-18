import csv
import math
import random
import re
from os import getcwd
from os.path import dirname
from typing import Iterator

from esrally.track.params import ParamSource

QUERIES_DIRNAME: str = dirname(__file__)
QUERIES_FILENAME: str = f"{QUERIES_DIRNAME}/queries.csv"

SEARCH_APPLICATION_ROOT_ENDPOINT: str = "/_application/search_application"


def query_iterator(k: int) -> Iterator[str]:
    with open(QUERIES_FILENAME) as queries_file:
        csv_reader = csv.reader(queries_file)
        next(csv_reader)
        queries_with_probabilities = list(tuple(line) for line in csv_reader)

        queries = [query for query, _ in queries_with_probabilities]
        probabilities = [float(probability) for _, probability in queries_with_probabilities]

        for query in random.choices(queries, weights=probabilities, k=k):
            yield query


class SearchApplicationParams:
    def __init__(self, track, params):
        self.indices = params.get("indices", track.index_names())
        self.name = params.get("search-application", f"{self.indices[0]}-search-application")


class CreateSearchApplicationParamSource(ParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self.search_application_params = SearchApplicationParams(track, params)

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        return {
            "method": "PUT",
            "path": f"{SEARCH_APPLICATION_ROOT_ENDPOINT}/{self.search_application_params.name}",
            "body": {"indices": self.search_application_params.indices},
        }


class SearchApplicationSearchParamSource(ParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self.search_application_params = SearchApplicationParams(track, params)
        self._queries_iterator = None

    def size(self):
        return self._params.get("iterations", 10000)

    def partition(self, partition_index, total_partitions):
        if self._queries_iterator is None:
            partition_size = math.ceil(self.size() / total_partitions)
            self._queries_iterator = query_iterator(partition_size)
        return self

    def params(self):
        # remover special chars from the query + lowercase
        query = re.sub("[^0-9a-zA-Z]+", " ", next(self._queries_iterator)).lower()
        return {
            "method": "POST",
            "path": f"{SEARCH_APPLICATION_ROOT_ENDPOINT}/{self.search_application_params.name}/_search",
            "body": {"params": {"query_string": query}},
        }


class QueryParamSource:
    def __init__(self, track, params, **kwargs):
        if len(track.indices) == 1:
            default_index = track.indices[0].name
            if len(track.indices[0].types) == 1:
                default_type = track.indices[0].types[0].name
            else:
                default_type = None
        else:
            default_index = "_all"
            default_type = None

        self._index_name = params.get("index", default_index)
        self._type_name = params.get("type", default_type)
        self._cache = params.get("cache", False)
        self._params = params
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        if self._queries_iterator is None:
            partition_size = math.ceil(self._params.get("iterations", 10000) / total_partitions)
            self._queries_iterator = query_iterator(partition_size)
        return self

    def params(self):
        query_str = re.sub("[^0-9a-zA-Z]+", " ", next(self._queries_iterator)).lower()
        result = {
            "body": {"query": {"query_string": {"query": query_str, "default_field": self._params["search_fields"]}}},
            "size": self._params["size"],
        }

        if "cache" in self._params:
            result["cache"] = self._params["cache"]

        return result


def register(registry):
    registry.register_param_source("query-string-search", QueryParamSource)
    registry.register_param_source("create-search-application-param-source", CreateSearchApplicationParamSource)
    registry.register_param_source("search-application-search-param-source", SearchApplicationSearchParamSource)

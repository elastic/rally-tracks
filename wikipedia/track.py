import csv
import math
import random
import re
from os import getcwd
from os.path import dirname
from typing import Iterator, List

from esrally.track.params import ParamSource

QUERIES_DIRNAME: str = dirname(__file__)
QUERIES_FILENAME: str = f"{QUERIES_DIRNAME}/queries.csv"

SEARCH_APPLICATION_ROOT_ENDPOINT: str = "/_application/search_application"
QUERY_RULES_ENDPOINT: str = "/_query_rules"

QUERY_CLEAN_REXEXP = regexp = re.compile("[^0-9a-zA-Z]+")


def query_samples(k: int, random_seed: int = None) -> List[str]:
    with open(QUERIES_FILENAME) as queries_file:
        csv_reader = csv.reader(queries_file)
        next(csv_reader)
        queries_with_probabilities = list(tuple(line) for line in csv_reader)

        queries = [QUERY_CLEAN_REXEXP.sub(" ", query).lower() for query, _ in queries_with_probabilities]
        probabilities = [float(probability) for _, probability in queries_with_probabilities]
        random.seed(random_seed)

        return random.choices(queries, weights=probabilities, k=k)


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


class QueryRulesetParams:
    def __init__(self, track, params):
        self.indices = params.get("indices", track.index_names())
        self.ruleset_id = params.get("ruleset_id")
        self.ruleset_size = params.get("ruleset_size")


class QueryIteratorParamSource(ParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self._batch_size = self._params.get("batch_size", 100000)
        self._random_seed = self._params.get("seed", None)
        self._sample_queries = query_samples(self._batch_size, self._random_seed)
        self._queries_iterator = None

    def size(self):
        return None

    def partition(self, partition_index, total_partitions):
        if self._queries_iterator is None:
            self._queries_iterator = iter(self._sample_queries)
        return self


class SearchApplicationSearchParamSource(QueryIteratorParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self.search_application_params = SearchApplicationParams(track, params)

    def params(self):
        try:
            query = next(self._queries_iterator)
            return {
                "method": "POST",
                "path": f"{SEARCH_APPLICATION_ROOT_ENDPOINT}/{self.search_application_params.name}/_search",
                "body": {
                    "params": {
                        "query_string": query,
                    },
                },
            }
        except StopIteration:
            self._queries_iterator = iter(self._sample_queries)
            return self.params()


class QueryParamSource(QueryIteratorParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self._index_name = params.get("index", track.indices[0].name if len(track.indices) == 1 else "_all")
        self._cache = params.get("cache", True)

    def params(self):
        try:
            result = {
                "body": {
                    "query": {"query_string": {"query": next(self._queries_iterator), "default_field": self._params["search-fields"]}}
                },
                "size": self._params["size"],
                "index": self._index_name,
                "cache": self._cache,
            }

            return result
        except StopIteration:
            self._queries_iterator = iter(self._sample_queries)
            return self.params()


class CreateQueryRulesetParamSource(ParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self.query_ruleset_params = QueryRulesetParams(track, params)

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        rules = []
        for i in range(self.query_ruleset_params.ruleset_size):
            # Note: `AccessibleComputing` is one of the _ids indexed in the dataset
            rule = {
                "rule_id": "rule_{{i}}",
                "type": "pinned",
                "criteria": [{"type": "exact", "metadata": "rule_key", "values": [random.choice(["match", "no-match"])]}],
                "actions": {"ids": [random.choice(["AccessibleComputing", "pinned-miss"])]},
            }
            rules.append(rule)

        return {"method": "PUT", "path": f"{QUERY_RULES_ENDPOINT}/{self.query_ruleset_params.ruleset_id}", "body": {"rules": rules}}


class QueryRulesSearchParamSource(QueryIteratorParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self.query_ruleset_params = QueryRulesetParams(track, params)

    def params(self):
        try:
            query = next(self._queries_iterator)
            # TODO Update this to use current syntax with 8.15.0+
            return {
                "method": "POST",
                "path": "/_search",
                "body": {
                    "query": {
                        "rule_query": {
                            "match_criteria": {"rule_key": random.choice(["match", "no-match"])},
                            "ruleset_id": self.query_ruleset_params.ruleset_id,
                            "organic": {"query_string": {"query": query, "default_field": self._params["search-fields"]}},
                        }
                    },
                    "size": self._params["size"],
                },
            }
        except StopIteration:
            self._queries_iterator = iter(self._sample_queries)
            return self.params()


class PinnedSearchParamSource(QueryIteratorParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self.query_ruleset_params = QueryRulesetParams(track, params)

    def params(self):
        try:
            query = next(self._queries_iterator)
            # TODO Update this to use current syntax with 8.15.0+
            return {
                "method": "POST",
                "path": "/_search",
                "body": {
                    "query": {
                        "pinned": {
                            "organic": {"query_string": {"query": query, "default_field": self._params["search-fields"]}},
                            "ids": [random.choice(["AccessibleComputing", "pinned-miss"])],
                        }
                    },
                    "size": self._params["size"],
                },
            }
        except StopIteration:
            self._queries_iterator = iter(self._sample_queries)
            return self.params()


def register(registry):
    registry.register_param_source("query-string-search", QueryParamSource)
    registry.register_param_source("create-search-application-param-source", CreateSearchApplicationParamSource)
    registry.register_param_source("search-application-search-param-source", SearchApplicationSearchParamSource)
    registry.register_param_source("create-query-ruleset-param-source", CreateQueryRulesetParamSource)
    registry.register_param_source("query-rules-search-param-source", QueryRulesSearchParamSource)
    registry.register_param_source("pinned-search-param-source", PinnedSearchParamSource)

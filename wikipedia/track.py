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
SAMPLE_IDS_FILENAME: str = f"{QUERIES_DIRNAME}/ids.txt"

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


# ids file was created with the following command: grep _index pages-1k.json | jq .index._id | tr -d '"' | grep -v null > ids.txt
def ids_samples() -> List[str]:
    with open(SAMPLE_IDS_FILENAME, "r") as file:
        ids = {line.strip() for line in file}
    for i in range(100):
        ids.add(f"missing-id-{i}")
    return list(ids)


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


class CreateQueryRulesetParamSource(ParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self.query_ruleset_params = QueryRulesetParams(track, params)

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        ids = ids_samples()
        rules = []
        for i in range(self.query_ruleset_params.ruleset_size):
            rule = {
                "rule_id": "rule_{{i}}",
                "type": random.choice(["pinned", "exclude"]),
                "criteria": [{"type": "exact", "metadata": "rule_key", "values": [random.choice(["match", "no-match"])]}],
                "actions": {"ids": [random.choice(ids)]},
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
            return {
                "method": "POST",
                "path": "/_search",
                "body": {
                    "query": {
                        "rule": {
                            "match_criteria": {"rule_key": random.choice(["match", "no-match"])},
                            "ruleset_ids": [self.query_ruleset_params.ruleset_id],
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
        self.ids = ids_samples()

    def params(self):
        try:
            query = next(self._queries_iterator)
            return {
                "method": "POST",
                "path": "/_search",
                "body": {
                    "query": {
                        "pinned": {
                            "organic": {"query_string": {"query": query, "default_field": self._params["search-fields"]}},
                            "ids": [random.choice(self.ids)],
                        }
                    },
                    "size": self._params["size"],
                },
            }
        except StopIteration:
            self._queries_iterator = iter(self._sample_queries)
            return self.params()


class RetrieverParamSource(QueryIteratorParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self._index_name = params.get("index", track.indices[0].name if len(track.indices) == 1 else "_all")
        self._search_fields = self._params["search-fields"]
        self._rerank = params.get("rerank", False)
        self._reranker = params.get("reranker", "random_reranker")
        self._size = params.get("size", 20)

    def params(self):
        standard_retriever = {
            "standard": {"query": {"query_string": {"query": next(self._queries_iterator), "default_field": self._search_fields}}}
        }

        retriever = standard_retriever
        if self._rerank:
            retriever = {self._reranker: {"retriever": standard_retriever, "field": self._search_fields, "rank_window_size": self._size}}

        try:
            return {
                "method": "POST",
                "path": f"/{self._index_name}/_search",
                "body": {"retriever": retriever, "size": self._size},
            }
        except StopIteration:
            self._queries_iterator = iter(self._sample_queries)
            return self.params()


# TODO Add other queries, check default fields for search. Compare them with other DSL queries
class EsqlSearchParamSource(QueryIteratorParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self._index_name = params.get("index", track.indices[0].name if len(track.indices) == 1 else "_all")
        self._search_fields = self._params["search-fields"]
        self._size = params.get("size", 20)
        self._query_type = self._params["query-type"]

    def params(self):
        try:
            query = next(self._queries_iterator)
            if self._query_type == "query-string":
                query_body = f'QSTR("{ query }", {{"default_field": "{ self._search_fields }" }})'
            elif self._query_type == "match":
                query_body = f'MATCH(title, "{ query }") OR MATCH(content, "{ query }")'
            elif self._query_type == "kql":
                query_body = f'KQL("{ self._search_fields }:{ query }")'
            elif self._query_type == "term":
                query_body = f'TERM(title, "{ query }") OR TERM(content, "{ query }")'
            elif self._query_type == "match_phrase":
                query_body = f'MATCH_PHRASE(title, "{ query }") OR MATCH_PHRASE(content, "{ query }")'
            else:
                raise ValueError("Unknown query type: " + self._query_type)

            return {
                "query": f"FROM {self._index_name} METADATA _score | WHERE { query_body } | SORT _score DESC | LIMIT { self._size }",
            }

        except StopIteration:
            self._queries_iterator = iter(self._sample_queries)
            return self.params()


class QueryParamSource(QueryIteratorParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self._index_name = params.get("index", track.indices[0].name if len(track.indices) == 1 else "_all")
        self._cache = params.get("cache", False)
        self._query_type = self._params["query-type"]

    def params(self):
        try:
            query = next(self._queries_iterator)
            if self._query_type == "query-string":
                query_body = {"query_string": {"query": query, "default_field": self._params["search-fields"]}}
            elif self._query_type == "kql":
                query_body = {"kql": {"query": f'{ self._params["search-fields"] }:"{ query }"'}}
            elif self._query_type == "match":
                query_body = {"bool": {"should": [{"match": {"title": query}}, {"match": {"content": query}}]}}
            elif self._query_type == "multi_match":
                query_body = {"bool": {"should": [{"match": {"title": query}}, {"match": {"content": query}}]}}
            elif self._query_type == "term":
                query_body = {"bool": {"should": [{"term": {"title": query}}, {"term": {"content": query}}]}}
            elif self._query_type == "match_phrase":
                query_body = {"bool": {"should": [{"match_phrase": {"title": query}}, {"match_phrase": {"content": query}}]}}
            else:
                raise ValueError("Unknown query type: " + self._query_type)

        except StopIteration:
            self._queries_iterator = iter(self._sample_queries)
            return self.params()

        return {
            "body": {
                "query": query_body,
                "size": self._params["size"],
            },
            "index": self._index_name,
            "cache": self._cache,
        }


def register(registry):
    registry.register_param_source("query-search", QueryParamSource)
    registry.register_param_source("create-search-application-param-source", CreateSearchApplicationParamSource)
    registry.register_param_source("search-application-search-param-source", SearchApplicationSearchParamSource)
    registry.register_param_source("create-query-ruleset-param-source", CreateQueryRulesetParamSource)
    registry.register_param_source("query-rules-search-param-source", QueryRulesSearchParamSource)
    registry.register_param_source("pinned-search-param-source", PinnedSearchParamSource)
    registry.register_param_source("retriever-search", RetrieverParamSource)
    registry.register_param_source("esql-search", EsqlSearchParamSource)

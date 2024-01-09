import asyncio
import csv
import math
import random
import re
import json
from base64 import b64encode
from os import getcwd
from os.path import dirname
from typing import Iterator, List
from itertools import chain, islice

from esrally.track.params import ParamSource

def create_basic_auth_header(username, password):
    token = b64encode(f"{username}:{password}".encode('utf-8')).decode("ascii")
    return f'Basic {token}'

def batched(iterable, n):
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch

QUERIES_DIRNAME: str = dirname(__file__)
QUERIES_FILENAME: str = f"{QUERIES_DIRNAME}/queries.csv"

SEARCH_APPLICATION_ROOT_ENDPOINT: str = "/_application/search_application"

QUERY_CLEAN_REXEXP = regexp = re.compile("[^0-9a-zA-Z]+")

with open(f"{QUERIES_DIRNAME}/users.json") as f:
    USER_NAMES = json.load(f)

USERS = [
    {"username": v, "password": "ujd_rbh5quw7GWC@pjc"} for v in USER_NAMES
]
ROLE_TEMPLATE = {
    "indices": [
        {
            "names": ["wikipedia*"],
            "privileges": ["read", "all"],
            "query": {
                "template": {
                    "source": """{
            "bool": {
              "filter": {
                "bool": {
                  "should": [
                    {
                      "bool": {
                        "must_not": {
                          "exists": {
                            "field": "_allow_permissions"
                          }
                        }
                      }
                    },
                    {
                      "terms_set": {
                        "_allow_permissions.keyword": {
                          "terms": {{#toJson}}_user.metadata.documents-id{{/toJson}},
                          "minimum_should_match": 1
                        }
                      }
                    }
                    ]
                }
              }
            }
          }"""
                }
            },
        }
    ]
}
SOURCES = ['source-ed298d3e-457c-44df-b7c6-04638be4231a', 'source-8ad2a217-3813-40ce-8185-a5480a64aa3b', 'source-cd5fa06b-b9fb-43ea-9dea-1670315de46f', 'source-c2f59700-3dd6-49d4-b629-cbc626e78225', 'source-9707d274-c0cf-46f0-89cc-185375c6498b', 'source-7cb12757-5363-467b-a858-aeb274709d05', 'source-8ee293d4-5e3a-448e-84f5-43cd2f1b87ab', 'source-ea094ca8-4e20-445f-b87b-2dac5d5418a7', 'source-79c4ebce-cf52-49b6-9e3e-5dec0ad433e2', 'source-fae4090e-7040-442c-a4c7-5bcc2f4bff1c', 'source-6b4cf72b-ca41-4cb5-9db3-17308550755e', 'source-bf153937-e8b5-4d34-8801-4e57e8edfcf0', 'source-b6c92fdd-5b47-47e6-9e68-2b307ea2284d', 'source-ecd147f2-2a8f-4dd1-ac59-f8b85637797a', 'source-a2f7e3d0-af2a-4bce-ae17-789c0d20955f', 'source-3d134d50-29a7-4d0e-be8e-1e8e28cbeb3d', 'source-fc9ef042-2e1e-43db-9fdf-a096a4b2a65f', 'source-96d7b53d-6795-4c4e-ba8a-5e6de200039d', 'source-ed2078ef-e496-4cb9-a8fa-7442122f9f1b', 'source-b5c71063-be85-4f55-b185-5042c3360728']


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


class SearchApplicationSearchParamSourceWithUser(QueryIteratorParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self.search_application_params = SearchApplicationParams(track, params)
        self.users = int(params.get('users', 0)) or None
        if self.users is not None:
            self.users = self.users - 1

    def params(self):
        try:
            query = next(self._queries_iterator)
            return {
                "method": "POST",
                "headers": {"Authorization":
                    create_basic_auth_header(**USERS[0])},
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


async def create_users_and_roles(es, params):
    num_roles = int(params["roles"])

    for users_batch in batched(USERS[:(num_roles - 1)], 100):
        role_coros = (
            es.security.put_role(
                name=f"managed-role-search-{user['username']}",
                body=ROLE_TEMPLATE,
                refresh="wait_for")
            for user in users_batch
            )
        users_coros = (
            es.security.put_user(
                username=user["username"],
                params={
                    "password": user["password"],
                    "roles": [f"managed-role-search-{user['username']}"],
                    "metadata": { "documents-id": SOURCES}}
                )
            for user in users_batch
            )
        await asyncio.gather(*chain(role_coros, users_coros))
    await es.security.put_user(
            username=USERS[0]["username"],
            params={
                "password": USERS[0]["password"],
                "metadata": { "documents-id": SOURCES}}
            )

    await es.update_by_query(
        index="wikipedia",
        body={
            "script": {
                "source": "ctx._source._allow_permissions=params.sources;",
                "lang": "painless",
                "params": {"sources": SOURCES},
            },
        },
        conflicts="proceed",
        slices="24",
    )

    await es.indices.refresh(index="wikipedia")


async def reset_indices(es, params):
    for users_batch in batched(USERS, 100):
        users_coros = (
            es.security.delete_user(username=user['username'])
            for user in users_batch
            )
        role_coros = (
            es.security.delete_role(name=f"managed-role-search-{user['username']}")
            for user in users_batch
            )
        await asyncio.gather(*chain(role_coros, users_coros))

#    await es.update_by_query(
#        index="wikipedia",
#        body={
#            "script": {
#                "source": "ctx._source._allow_permissions = new ArrayList();",
#                "lang": "painless"
#            },
#        },
#        conflicts="proceed",
#        slices="10",
#        timeout="90m",
#        request_timeout=9600,
#    )
#
#    await es.indices.refresh(index="wikipedia")


def register(registry):
    registry.register_param_source("query-string-search", QueryParamSource)
    registry.register_param_source("create-search-application-param-source", CreateSearchApplicationParamSource)
    registry.register_param_source("search-application-search-param-source", SearchApplicationSearchParamSource)
    registry.register_param_source("search-application-search-param-source-with-user", SearchApplicationSearchParamSourceWithUser)
    registry.register_runner("create_users_and_roles", create_users_and_roles, async_runner=True)
    registry.register_runner("reset_indices", reset_indices, async_runner=True)

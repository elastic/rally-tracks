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
from itertools import chain, islice, cycle

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


class SearchParamSourceWithUser(QueryIteratorParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self.search_application_params = SearchApplicationParams(track, params)

    def params(self):
        try:
            query = next(self._queries_iterator)
            return {
                    "method": "POST",
                    "headers": {"Authorization":
                        create_basic_auth_header(username='435b173a-8283-4dc2-9c62-00f871866594', password='ujd_rbh5quw7GWC@pjc')},
                    "path": f"{SEARCH_APPLICATION_ROOT_ENDPOINT}/{self.search_application_params.name}/_search",
                    "body": {
                        "params": {
                            "query_string": query
                            }
                        }
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
    num_users = int(params["users"])

    await es.security.put_user(
        username='435b173a-8283-4dc2-9c62-00f871866594',
        params={
            "password": 'ujd_rbh5quw7GWC@pjc',
            "roles": ["managed-role-search"],
            "metadata": { "documents-id": ['435b173a-8283-4dc2-9c62-00f871866594']}}
        )

    if params.get('skip_perms'):
        return

    half_docs_num = int(num_users / 2)
    existing_permissions = []
    for i in range(0, half_docs_num):
        permissions_hash = None
        while True:
            permissions = [u['username'] for u in
                    random.sample(USERS[:num_users], k=half_docs_num)]

            permission_hash = hash('|'.join(sorted(permissions)))
            if permission_hash not in existing_permissions:
                existing_permissions.append(permission_hash)
                break

        await es.update_by_query(
            index="wikipedia",
            max_docs=1,
            body={
                "script": {
                    "source": "ctx._source._allow_permissions=params.permissions;",
                    "lang": "painless",
                    "params": {"permissions": permissions},
                },
                "query": {
                    "bool": {
                        "must_not": {
                            "exists" : {
                                "field": "_allow_permissions"
                                }
                            }
                        }
                    }
                },
        )
        await es.indices.refresh(index="wikipedia")


async def reset_indices(es, params):
#    for users_batch in batched(USERS[:1000], 100):
#        users_coros = (
#            es.security.delete_user(username=user['username'])
#            for user in users_batch
#            )
#        role_coros = (
#            es.security.delete_role(name=f"managed-role-search-{user['username']}")
#            for user in users_batch
#            )
#        await asyncio.gather(*users_coros)

    await es.update_by_query(
        index="wikipedia",
        body={
            "script": {
                "source": "ctx._source._allow_permissions = new ArrayList();",
                "lang": "painless"
                },
            "query": {
                "exists" : {
                    "field": "_allow_permissions"
                    }
                }
            },
        conflicts="proceed",
        slices="auto",
        timeout="90m",
        request_timeout=9600,
    )

    await es.indices.refresh(index="wikipedia")


def register(registry):
    registry.register_param_source("query-string-search", QueryParamSource)
    registry.register_param_source("create-search-application-param-source", CreateSearchApplicationParamSource)
    registry.register_param_source("search-application-search-param-source", SearchApplicationSearchParamSource)
    registry.register_param_source("search-application-search-param-source-with-user", SearchApplicationSearchParamSourceWithUser)
    registry.register_param_source("search-param-source-with-user", SearchParamSourceWithUser)
    registry.register_runner("create_users_and_roles", create_users_and_roles, async_runner=True)
    registry.register_runner("reset_indices", reset_indices, async_runner=True)

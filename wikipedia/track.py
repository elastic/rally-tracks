import csv
import math
import random
import re
import uuid
from base64 import b64encode
from os import getcwd
from os.path import dirname
from typing import Iterator, List

from esrally.track.params import ParamSource

QUERIES_DIRNAME: str = dirname(__file__)
QUERIES_FILENAME: str = f"{QUERIES_DIRNAME}/queries.csv"

SEARCH_APPLICATION_ROOT_ENDPOINT: str = "/_application/search_application"

QUERY_CLEAN_REXEXP = regexp = re.compile("[^0-9a-zA-Z]+")

ROLE_IDS = ["managed-role-search-{}".format(uuid.uuid4()) for x in range(0, 500000)]
USER_AUTH = {"username": "wikiuser", "password": "ujd_rbh5quw7GWC@pjc"}
AUTH_BEARER = b64encode(("{}:{}".format(*USER_AUTH.values())).encode('ascii'))
ROLE_TEMPLATE = {
    "indices": [
        {
            "names": ["wikipedia"],
            "privileges": ["read"],
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

    def params(self):
        try:
            query = next(self._queries_iterator)
            return {
                "method": "POST",
                "headers": {"Authorization": "Basic {}".format(AUTH_BEARER)},
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
    # For now we'll just work with one user with all the roles
    # num_users = params['users']

    await es.indices.refresh(index="wikipedia")
    doc_count = await es.count(index="wikipedia")

    num_roles = params["roles"]
    skip_roles = params["skip_roles"]

    user = None
    try:
        user = await es.security.get_user(username=USER_AUTH["username"])
    except:
        if not user:
            await es.security.put_user(
                username=USER_AUTH["username"], params={"password": USER_AUTH["password"], "roles": []}
            )

    for role in ROLE_IDS[skip_roles : num_roles - 1]:
        await es.security.put_role(name=role, body=ROLE_TEMPLATE, refresh="wait_for")
        await es.update_by_query(
            index="wikipedia",
            max_docs=int((doc_count["count"] / 100) * 1),
            body={
                "script": {
                    "source": "if (ctx._source._allow_permissions ==null){"
                    "ctx._source._allow_permissions =[params.role];} else "
                    "{ctx._source._allow_permissions.add(params.role)}",
                    "lang": "painless",
                    "params": {"role": role},
                },
                "query": {"function_score": {"query": {"match_all": {}}, "random_score": {}}},
            },
            conflicts="proceed",
        )

    await es.security.put_user(
        username=USER_AUTH["username"], params={"roles": ROLE_IDS[0 : num_roles - 1]}
    )

    await es.indices.refresh(index="wikipedia")


async def reset_indices(es, params):
    roles = await es.security.get_role()
    for role in roles:
        if role.startswith("managed-role-search-"):
            await es.security.delete_role(name=role)

    await es.update_by_query(
        index="wikipedia",
        body={
            "query": {"exists": {"field": "_allow_permissions"}},
            "script": {"source": "ctx._source._allow_permissions = new ArrayList();", "lang": "painless"},
        },
        conflicts="proceed",
    )

    await es.indices.refresh(index="wikipedia")

    await es.security.put_user(
        username=USER_AUTH["username"], params={"password": USER_AUTH["password"], roles: []}
    )


def register(registry):
    registry.register_param_source("query-string-search", QueryParamSource)
    registry.register_param_source("create-search-application-param-source", CreateSearchApplicationParamSource)
    registry.register_param_source("search-application-search-param-source", SearchApplicationSearchParamSource)
    registry.register_param_source("search-application-search-param-source-with-user", SearchApplicationSearchParamSourceWithUser)
    registry.register_runner("create_users_and_roles", create_users_and_roles, async_runner=True)
    registry.register_runner("reset_indices", reset_indices, async_runner=True)

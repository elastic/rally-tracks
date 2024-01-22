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
SOURCES = ['c9410aef-86c0-4689-a0dd-7f50d97a1fd0', '3a842aef-0d58-4b1d-8a82-c2c33b48d8cd', '765de6d0-8e98-4bf4-8a33-855d920d76d5', '46a4d054-e265-470c-b0d2-c86ba9d919b3', '20e04c3b-a16a-4145-b86f-20ac208f73ff', '1969f3b0-9981-4920-a8f0-3a43ac922a70', 'fa6ead5a-925c-4a7e-bda4-2c9bc09f6056', '95b2078a-5c7a-4198-ba61-5183e6af1e28', '0ad14cde-97a4-46cf-a034-676d6b8ddf32', 'eaca4f78-4c84-41ab-8c2e-5d873dda47f0', '76e36528-42c2-4e71-b283-a93d8c051187', '574653d3-bef8-434a-bd89-34e3481e99f2', 'de7cd919-3c05-45cb-b60f-92de391c27a6', '5dedb962-8f6f-414f-b859-b89693d4ae90', '5bcc9fbc-fee7-4d87-bbad-5b5d86de6397', '046887a6-c6d9-4a30-9f37-3142c1db2ea2', 'f467eb4b-9e0d-4b07-8c56-4b89bacba49c', '6fe2163a-0799-4fba-a5e1-8022acd1d712', '692569f5-8cea-4b5e-a0aa-426c1e566759', '488c264f-3d29-4598-918f-c0f783ff5ba7', 'd68e3ab7-cd54-4345-8d4a-698c144c098d', '1cb302f3-ddb0-47cc-8d38-2945d743dd42', '58383f3a-581d-4236-8eab-91b86275a3cb', 'c5a77c71-285a-44a6-9fd2-f2fd37483d23', '4a766e08-702b-42c8-9484-d889bb68df33', 'fd4c2274-4ce2-4e7a-8224-012612fa0d3d', '0d7c2fd6-dc8d-44c0-b3e2-6a7aa71900ac', '76a29cf1-fd5c-4b73-a6c1-f243e7141905', '3ce05431-e1d5-4c38-b249-722b4a55d3f3', '22bb8f47-9055-48ab-8865-e88a9271bb4c', 'b30661e8-4e7e-4bf2-b73f-2fd2c04d44f0', '7557f4b6-e29f-4519-9971-02d53a3796e2', '2bb47ac8-9b12-401e-9ca3-36c96d6107ee', '76b6fb5a-7024-4b36-b35a-ae810fc51b82', 'e97b36a1-6368-4c1c-b2c2-1899fcf36835', '677bc44d-09c2-4722-89ca-0ef96c074717', '5dbf81bc-261b-4dc4-88a1-0f09c1ee990d', '6891b038-7c86-4a78-b9ec-376dc0abc4e9', '368108d0-7f5b-4ba1-b0a8-f3545845e74c', 'a9bc7483-1e07-476b-b274-835a1a24232b', 'cee3c0e1-7c62-447d-b516-97ae8b21b308', '2db11e34-952f-4aa0-9aed-f2b31d5e54ea', 'af6fe3e8-4761-446c-b0c6-0483fdbceb1c', '7b3afcbf-5c67-4e31-b156-d3660efcab45', 'b0547e41-e0a3-422d-a2ee-2952a1437363', '49af95e4-9cea-4c43-9909-347d853b9058', 'b44c649b-8a56-48b8-8923-f4c57bbf0fa8', '3b4052f6-9dc8-49c5-acd8-74bedd9bf289', 'dac200fc-6807-4208-8923-ed99c7751cb2', '4bc364ab-723b-4ce6-81ab-d60ecf7c055c', '188a080a-c589-4d7b-9275-2469ab47ed9a', '9097cad3-60f0-4e32-80c3-83a9f2225c1f', '07c0581c-c312-4828-b7af-45f59f528c53', '645479e2-deb9-42ab-9b14-fd1d3c651cf3', 'cb6b58c8-1fc9-4000-b7d2-73a09e25e1d9', 'ced9130a-4349-42ff-9162-843520ea106b', 'b5fba4b2-2258-486b-8d99-aaa891300a49', '22e0ffad-8ee1-4e88-b210-cda3815680f9', '95531ac5-d8ff-41f9-aff1-6de8440dda8d', '125515ab-a18f-44b6-a0bb-41a7e729b8f2', '50deb9c3-9fa7-4237-9d4a-e131ff6a6767', '0a07b04c-d20c-4df6-8b25-2498c48326e1', '8efbde91-7443-4936-85b9-ec12a802cd3b', '7144b9eb-e1be-46fd-acc4-98b48fa2913a', 'f0cf83a0-2cb8-4594-bee3-f6aefe36583f', '1ac197fb-efc8-4b00-b4eb-6a64fcebc589', 'b41d19a3-25dd-4a03-a755-d3fbae2e3379', 'c3d602cc-f0c8-4cbf-bb50-f70e34d9ea31', 'f52a1d35-c8f0-497f-84b7-e54c0c93bd23', '98ad1c89-3cca-415f-9d41-391d35faf287', '21a031fe-0ff9-4711-bd4f-46dd30154a55', '29e8de46-b6c9-4f54-b8c2-fdf22161ee8e', '3dee4bc2-82c5-47c3-8eb4-4c510e02144b', 'de2dc469-32b9-456a-b24e-c673e56f919d', 'd2986bc7-deb1-4fa2-bdfa-e44e244be716', '10ed4616-a204-4eab-80d8-1f22f9440908', 'd7b9a51d-7c06-464c-b341-dbd8c9fc4e4c', 'c693cafb-d187-4f0c-a24e-7c7d586f0b30', '64c842e3-950c-45ae-a018-334c9679f90b', '8486fe2d-8d58-452e-8d43-dcb6c3028f10', '47eb49e9-2db5-41e4-bb6b-5c794e0166fa', '0b3c075a-a40d-4b2d-a965-c26d11ed5f11', 'a117d901-26e1-4fd8-878f-af0ef4868f53', '4d629f8d-3453-471b-aba5-8badfa809027', '34bded72-05da-462a-a501-ca82e0cadf88', '4a030dba-f34b-4afa-9aab-d7d9b84b1c00', '1e985333-94f1-444c-a629-f251b018a117', 'e585cf89-02fd-4767-995c-f66e5e5aedb4', '24296170-6b25-457f-ae82-e6d01fa7d65d', 'bdb18b24-ab86-451c-9fc0-40501cfa1bdb', '1442a628-fd4e-4e23-a229-b5d53a571d6f', '865083fa-429f-4e02-a47b-4d1e08f28a22', 'c8648845-9cf4-47a0-a64d-b6de6f179123', '2eb340bb-dcce-4a84-b630-52f3dd9611d7', 'ba5da736-f606-4591-acbb-974597aacd16', '374cccdd-bf00-436b-9d2c-72717aa14225', '25a7b3b2-6e76-40e2-a81e-1efdf4862a91', '2a68b74b-2f03-48c1-bd90-6eed44df0581', '3bf8e20b-9500-4136-bef9-1f307403e837', '0db49076-f20e-465b-b8b1-ccb63eb0c2d2']


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

        self.users = iter(USERS)

    def params(self):
        try:
            query = next(self._queries_iterator)
            return {
                    "method": "POST",
                    "headers": {"Authorization": create_basic_auth_header(**next(self.users))},
                    "path": "/wikipedia/_search",
                    "body": {
                        "query": {
                            "query_string": query,
                            "exists" : {
                                "field": "_allow_permissions"
                                }
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

    await es.security.put_role(
        name="managed-role-search",
        body=ROLE_TEMPLATE,
        refresh="wait_for")

    sources1 = SOURCES[0:50]
    sources2 = SOURCES[50:100]
    sourcs = cycle(sources1, sources2)

    for users_batch in batched(USERS[0:num_users], 100):
        users_coros = (
            es.security.put_user(
                username=user["username"],
                params={
                    "password": user["password"],
                    "roles": ["managed-role-search"],
                    "metadata": { "documents-id": random.sample(next(sources),4)}}
                )
            for user in users_batch
            )
        await asyncio.gather(*users_coros)

    await es.update_by_query(
        index="wikipedia",
        max_docs=100000,
        body={
            "script": {
                "source": "ctx._source._allow_permissions=params.sources;",
                "lang": "painless",
                "params": {"sources": SOURCES[50:100]},
            },
        },
        conflicts="proceed",
        slices="auto",
    )

    await es.update_by_query(
        index="wikipedia",
        max_docs=50000,
        body={
            "script": {
                "source": "ctx._source._allow_permissions=params.sources;",
                "lang": "painless",
                "params": {"sources": SOURCES[0:50]},
            },
        },
        conflicts="proceed",
        slices="auto",
    )

    await es.indices.refresh(index="wikipedia")


async def reset_indices(es, params):
    for users_batch in batched(USERS[:1000], 100):
        users_coros = (
            es.security.delete_user(username=user['username'])
            for user in users_batch
            )
        role_coros = (
            es.security.delete_role(name=f"managed-role-search-{user['username']}")
            for user in users_batch
            )
        await asyncio.gather(*users_coros)

    await es.update_by_query(
        index="wikipedia",
        body={
            "script": {
                "source": "ctx._source._allow_permissions = new ArrayList();",
                "lang": "painless"
            },
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

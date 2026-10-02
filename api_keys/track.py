"""
Rally track for benchmarking Elasticsearch API key authentication.

The track creates a population of native roles, native users (the API key owners) and REST API keys, then measures
``GET /_security/_authenticate`` with those API keys. All generated data is deterministic for a given ``seed`` so that
races against different Elasticsearch revisions see exactly the same population and request mix.

Rally runs one worker process per CPU core and spreads clients across them, so in-memory state cannot be shared between
tasks or clients. API keys are therefore persisted to disk by the ``create-api-keys`` task (one JSONL key file per creation
client) and lazily loaded by the parameter source that feeds the authentication tasks.
"""

import asyncio
import base64
import json
import logging
import os
import random
import threading
import time
from dataclasses import dataclass

import elasticsearch
from esrally.track.params import ParamSource

LOGGER = logging.getLogger(__name__)

DEFAULT_API_KEYS_DIR = "~/.rally/benchmarks/data/api_keys"
USER_PASSWORD = "api-keys-benchmark-password"
INVALID_API_KEY_SECRET = "invalid-api-key-secret"
KEY_FILE_TEMPLATE = "api-keys.{client}.jsonl"
STATS_SNAPSHOT_FILE = "security-stats-before.json"
AUTHENTICATE_PATH = "/_security/_authenticate"
SECURITY_CRYPTO_THREAD_POOL = "security-crypto"

CLUSTER_PRIVILEGES = [
    "monitor",
    "manage_index_templates",
    "manage_ilm",
    "manage_ingest_pipelines",
    "read_pipeline",
    "manage_own_api_key",
    "manage_logstash_pipelines",
    "monitor_ml",
    "monitor_transform",
    "read_ccr",
]
INDEX_PRIVILEGES = ["read", "view_index_metadata", "write", "create_doc", "index", "monitor", "maintenance"]
INDEX_PATTERN_TEMPLATES = ["logs-{app}-*", "metrics-{app}-*", "{app}-*", "*-{app}-*", "{app}"]


# ---------------------------------------------------------------------------------------------------------------------
# Deterministic data generation
# ---------------------------------------------------------------------------------------------------------------------


def _index_patterns(rng, count):
    patterns = []
    for _ in range(count):
        app = f"app{rng.randrange(1000)}"
        patterns.append(rng.choice(INDEX_PATTERN_TEMPLATES).format(app=app))
    return patterns


def role_definition(rng):
    """Generates the ``cluster`` and ``indices`` sections of a role (or role descriptor) from the given RNG."""
    return {
        "cluster": sorted(rng.sample(CLUSTER_PRIVILEGES, k=rng.randint(1, 3))),
        "indices": [
            {
                "names": _index_patterns(rng, rng.randint(1, 2)),
                "privileges": sorted(rng.sample(INDEX_PRIVILEGES, k=rng.randint(1, 3))),
            }
            for _ in range(rng.randint(1, 3))
        ],
    }


def role_name(index):
    # namespaced to this track so that it can share a persistent cluster with other security tracks (e.g. has_privileges)
    return f"api_keys_role_{index}"


def user_name(index):
    return f"api_keys_user_{index}"


def role_descriptor_template(seed, template_index):
    """
    Returns the role descriptors assigned to API keys that use the given template. The result is a deterministic function
    of (seed, template_index), hence all API keys sharing a template have byte-identical role descriptors and share the
    corresponding role descriptor and role cache entries in Elasticsearch.
    """
    rng = random.Random(f"{seed}:role-descriptors:{template_index}")
    descriptors = {f"rd_{template_index}_a": role_definition(rng)}
    if rng.random() < 0.5:
        descriptors[f"rd_{template_index}_b"] = role_definition(rng)
    return descriptors


@dataclass(frozen=True)
class ApiKeySpec:
    index: int
    owner: str
    rd_template: int | None

    @property
    def name(self):
        return f"api-key-{self.index}"

    def role_descriptors(self, seed):
        if self.rd_template is None:
            # an empty set of role descriptors means the API key inherits all privileges of its owner
            return {}
        return role_descriptor_template(seed, self.rd_template)

    @property
    def metadata(self):
        return {
            "benchmark": "api_keys",
            "key_index": self.index,
            "owner": self.owner,
            "role_descriptors": "inherited" if self.rd_template is None else f"template_{self.rd_template}",
        }


def api_key_spec(index, seed, num_users, num_rd_templates, assigned_rd_ratio):
    """Derives the owner and role descriptor template of the API key with the given index. Deterministic per (seed, index)."""
    rng = random.Random(f"{seed}:api-key:{index}")
    owner = user_name(index % num_users)
    rd_template = index % num_rd_templates if num_rd_templates > 0 and rng.random() < assigned_rd_ratio else None
    return ApiKeySpec(index=index, owner=owner, rd_template=rd_template)


def encode_api_key(api_key_id, api_key_secret):
    return base64.b64encode(f"{api_key_id}:{api_key_secret}".encode("utf-8")).decode("utf-8")


# ---------------------------------------------------------------------------------------------------------------------
# API key store on disk
# ---------------------------------------------------------------------------------------------------------------------


def api_keys_dir(params):
    return os.path.expanduser(params.get("api_keys_dir", DEFAULT_API_KEYS_DIR))


def key_file(directory, client_index):
    return os.path.join(directory, KEY_FILE_TEMPLATE.format(client=client_index))


_KEY_CACHE = {}
_KEY_CACHE_LOCK = threading.Lock()


def load_api_keys(directory, create_clients):
    """
    Loads all API keys written by the ``create-api-keys`` task. Only the key files written by the current configuration
    (``create_clients``) are read so that stale files from earlier races with more creation clients are ignored. The
    result is cached per process as every client in a worker process needs the same list.
    """
    cache_key = (directory, create_clients)
    with _KEY_CACHE_LOCK:
        if cache_key in _KEY_CACHE:
            return _KEY_CACHE[cache_key]
        records = []
        for client_index in range(create_clients):
            path = key_file(directory, client_index)
            if not os.path.exists(path):
                raise FileNotFoundError(f"API key file [{path}] does not exist. Ensure that the create-api-keys task ran before.")
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
        if not records:
            raise ValueError(f"No API keys found in [{directory}]. Ensure that the create-api-keys task ran before.")
        # creation clients write in interleaved order; order by key index so that key selection is independent of the file layout
        records.sort(key=lambda record: record["index"])
        keys = [(record["id"], record["encoded"]) for record in records]
        LOGGER.info("Loaded [%d] API keys from [%d] key file(s) in [%s].", len(keys), create_clients, directory)
        _KEY_CACHE[cache_key] = keys
        return keys


# ---------------------------------------------------------------------------------------------------------------------
# Parameter sources
# ---------------------------------------------------------------------------------------------------------------------


class ApiKeyCreateParamSource(ParamSource):
    """
    Partitions the API key indices among the creation clients. Every invocation of ``params()`` yields a batch of API
    key indices that the ``create-api-keys`` runner creates concurrently and appends to the key file of the client.
    """

    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self.num_api_keys = int(params.get("num_api_keys", 10000))
        self.batch_size = int(params.get("create_batch_size", 100))
        self.assigned_rd_ratio = float(params.get("assigned_rd_ratio", 0.5))
        if self.num_api_keys <= 0:
            raise ValueError("num_api_keys must be positive")
        if self.batch_size <= 0:
            raise ValueError("create_batch_size must be positive")
        if not 0 <= self.assigned_rd_ratio <= 1:
            raise ValueError("assigned_rd_ratio must be in [0, 1]")
        self.directory = api_keys_dir(params)
        self.partition_index = None
        self.total_partitions = None
        self._batches = None
        self._next_batch = 0
        self._key_file = None
        self._key_file_reset = False

    def partition(self, partition_index, total_partitions):
        partitioned = ApiKeyCreateParamSource(self.track, self._params)
        partitioned.partition_index = partition_index
        partitioned.total_partitions = total_partitions
        indices = list(range(partition_index, self.num_api_keys, total_partitions))
        partitioned._batches = [indices[i : i + self.batch_size] for i in range(0, len(indices), self.batch_size)]
        partitioned._key_file = key_file(self.directory, partition_index)
        return partitioned

    def size(self):
        return len(self._batches) if self._batches is not None else None

    def params(self):
        if self._batches is None:
            raise ValueError("ApiKeyCreateParamSource must be partitioned before use")
        if not self._key_file_reset:
            # drop keys from earlier races; every client owns exactly one key file and truncates it before writing to it.
            # The files contain usable API key credentials, so keep them readable by the current user only.
            os.makedirs(self.directory, exist_ok=True)
            os.close(os.open(self._key_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600))
            os.chmod(self._key_file, 0o600)
            self._key_file_reset = True
        if self._next_batch >= len(self._batches):
            raise StopIteration()
        batch = self._batches[self._next_batch]
        self._next_batch += 1
        return {
            "key_indices": batch,
            "key_file": self._key_file,
            "seed": self._params.get("seed", 42),
            "num_users": int(self._params.get("num_users", 100)),
            "num_rd_templates": int(self._params.get("num_rd_templates", 50)),
            "assigned_rd_ratio": self.assigned_rd_ratio,
            "api_key_expiration": self._params.get("api_key_expiration"),
        }


class ApiKeyAuthenticateParamSource(ParamSource):
    """
    Provides the encoded API key to authenticate with. Supported access patterns:

    * ``sweep``: every API key exactly once across all clients (cache priming / cold-path measurement).
    * ``uniform``: uniformly random key per request. When the population exceeds the API key cache capacity this is the
      worst case for the LRU caches.
    * ``hotset``: ``hot_ratio`` of the requests target ``hot_fraction`` of the keys, the rest is uniform over the other keys.

    ``invalid_credentials_ratio`` requests (uniform and hotset patterns) use a wrong secret for an existing key id.
    """

    ACCESS_PATTERNS = ("sweep", "uniform", "hotset")

    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self.mode = params.get("access_pattern", "uniform")
        if self.mode not in self.ACCESS_PATTERNS:
            raise ValueError(f"Unknown access pattern [{self.mode}]. Supported access patterns are {self.ACCESS_PATTERNS}.")
        self.directory = api_keys_dir(params)
        self.create_clients = int(params.get("create_clients", 8))
        self.seed = params.get("seed", 42)
        self.hot_fraction = float(params.get("hot_fraction", 0.01))
        self.hot_ratio = float(params.get("hot_ratio", 0.9))
        self.invalid_credentials_ratio = float(params.get("invalid_credentials_ratio", 0.0))
        if not 0 < self.hot_fraction <= 1:
            raise ValueError("hot_fraction must be in (0, 1]")
        if not 0 <= self.hot_ratio <= 1:
            raise ValueError("hot_ratio must be in [0, 1]")
        if not 0 <= self.invalid_credentials_ratio <= 1:
            raise ValueError("invalid_credentials_ratio must be in [0, 1]")
        self.partition_index = 0
        self.total_partitions = 1
        self._rng = None
        self._keys = None
        self._hot_keys = None
        self._cold_keys = None
        self._sweep_position = 0

    def partition(self, partition_index, total_partitions):
        partitioned = ApiKeyAuthenticateParamSource(self.track, self._params)
        partitioned.partition_index = partition_index
        partitioned.total_partitions = total_partitions
        partitioned._rng = random.Random(f"{self.seed}:authenticate:{partition_index}")
        return partitioned

    def _ensure_loaded(self):
        if self._keys is not None:
            return
        all_keys = load_api_keys(self.directory, self.create_clients)
        if self.mode == "sweep":
            self._keys = all_keys[self.partition_index :: self.total_partitions]
        else:
            self._keys = all_keys
            if self.mode == "hotset":
                shuffled = list(all_keys)
                random.Random(f"{self.seed}:hotset").shuffle(shuffled)
                hot_count = max(1, int(len(shuffled) * self.hot_fraction))
                self._hot_keys = shuffled[:hot_count]
                self._cold_keys = shuffled[hot_count:] or self._hot_keys
        if self._rng is None:
            self._rng = random.Random(f"{self.seed}:authenticate:{self.partition_index}")

    def size(self):
        if self.mode == "sweep":
            self._ensure_loaded()
            return len(self._keys)
        return None

    def _next_key(self):
        if self.mode == "sweep":
            if self._sweep_position >= len(self._keys):
                raise StopIteration()
            key = self._keys[self._sweep_position]
            self._sweep_position += 1
            return key
        if self.mode == "hotset":
            keys = self._hot_keys if self._rng.random() < self.hot_ratio else self._cold_keys
            return keys[self._rng.randrange(len(keys))]
        return self._keys[self._rng.randrange(len(self._keys))]

    def params(self):
        self._ensure_loaded()
        api_key_id, encoded = self._next_key()
        expect_failure = False
        if self.mode != "sweep" and self.invalid_credentials_ratio > 0 and self._rng.random() < self.invalid_credentials_ratio:
            encoded = encode_api_key(api_key_id, INVALID_API_KEY_SECRET)
            expect_failure = True
        return {"encoded_api_key": encoded, "expect_failure": expect_failure}


# ---------------------------------------------------------------------------------------------------------------------
# Runners
# ---------------------------------------------------------------------------------------------------------------------


async def _gather_in_chunks(coroutine_factories, chunk_size):
    results = []
    for start in range(0, len(coroutine_factories), chunk_size):
        chunk = coroutine_factories[start : start + chunk_size]
        results.extend(await asyncio.gather(*(factory() for factory in chunk)))
    return results


async def _with_retries(operation, description, max_attempts=5, initial_backoff=0.2, retry_on_timeout=True):
    """
    Retries an operation with exponential backoff when Elasticsearch rejected it (HTTP 429) or had no shard available
    (HTTP 503); in both cases the request was not executed. Timeouts are only retried if ``retry_on_timeout`` is set:
    a timed out request may have been executed, so this must stay disabled for non-idempotent operations such as creating
    API keys, where a retry could create an unrecorded duplicate.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            return await operation()
        except elasticsearch.ApiError as e:
            if attempt >= max_attempts or e.status_code not in (429, 503):
                raise
            LOGGER.warning("[%s] failed with HTTP %s (attempt %d/%d), retrying.", description, e.status_code, attempt, max_attempts)
        except elasticsearch.ConnectionTimeout:
            if not retry_on_timeout or attempt >= max_attempts:
                raise
            LOGGER.warning("[%s] timed out (attempt %d/%d), retrying.", description, attempt, max_attempts)
        await asyncio.sleep(initial_backoff * (2 ** (attempt - 1)) * (1 + random.random()))


async def create_roles_and_users(es, params):
    """Creates the native roles and the native users that own the API keys."""
    seed = params.get("seed", 42)
    num_roles = int(params.get("num_roles", 100))
    num_users = int(params.get("num_users", 100))
    roles_per_user = int(params.get("roles_per_user", 2))
    kibana_app_privileges = bool(params.get("kibana_app_privileges", False))
    num_kibana_spaces = int(params.get("num_kibana_spaces", 100))
    if num_roles <= 0 or num_users <= 0:
        raise ValueError("num_roles and num_users must be positive")
    if roles_per_user > num_roles:
        raise ValueError(f"roles_per_user ({roles_per_user}) cannot exceed num_roles ({num_roles})")

    rng = random.Random(f"{seed}:roles")
    spaces = [f"space:space{i}" for i in range(num_kibana_spaces)]
    role_requests = []
    for i in range(num_roles):
        definition = role_definition(rng)
        kwargs = {"name": role_name(i), "cluster": definition["cluster"], "indices": definition["indices"]}
        if kibana_app_privileges:
            kwargs["applications"] = [{"application": "kibana-.kibana", "privileges": ["all"], "resources": rng.sample(spaces, k=1)}]
        role_requests.append(kwargs)

    user_rng = random.Random(f"{seed}:users")
    role_names = [role_name(i) for i in range(num_roles)]
    user_requests = [
        {"username": user_name(i), "password": USER_PASSWORD, "roles": sorted(user_rng.sample(role_names, k=roles_per_user))}
        for i in range(num_users)
    ]

    def put_role(kwargs):
        return lambda: _with_retries(lambda: es.security.put_role(**kwargs), f"put role {kwargs['name']}")

    def put_user(kwargs):
        return lambda: _with_retries(lambda: es.security.put_user(**kwargs), f"put user {kwargs['username']}")

    await _gather_in_chunks([put_role(kwargs) for kwargs in role_requests], chunk_size=25)
    await _gather_in_chunks([put_user(kwargs) for kwargs in user_requests], chunk_size=25)
    LOGGER.info("Created [%d] roles and [%d] users.", num_roles, num_users)
    return {"weight": num_roles + num_users, "unit": "ops", "roles": num_roles, "users": num_users}


async def create_api_keys(es, params):
    """Creates a batch of API keys (via the grant API, on behalf of their owners) and appends them to the client's key file."""
    key_indices = params["key_indices"]
    seed = params["seed"]
    num_users = params["num_users"]
    num_rd_templates = params["num_rd_templates"]
    assigned_rd_ratio = params["assigned_rd_ratio"]
    expiration = params.get("api_key_expiration")

    async def create_one(index):
        spec = api_key_spec(index, seed, num_users, num_rd_templates, assigned_rd_ratio)
        api_key = {"name": spec.name, "role_descriptors": spec.role_descriptors(seed), "metadata": spec.metadata}
        if expiration:
            api_key["expiration"] = expiration
        # creating an API key is not idempotent: never retry after a timeout (see _with_retries)
        response = await _with_retries(
            lambda: es.security.grant_api_key(grant_type="password", username=spec.owner, password=USER_PASSWORD, api_key=api_key),
            f"grant API key {spec.name}",
            retry_on_timeout=False,
        )
        return {
            "index": index,
            "id": response["id"],
            "encoded": response["encoded"],
            "owner": spec.owner,
            "rd_template": spec.rd_template,
        }

    records = await asyncio.gather(*(create_one(index) for index in key_indices))
    with open(params["key_file"], "a", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return {"weight": len(records), "unit": "keys"}


async def authenticate_api_key(es, params):
    """Calls ``GET /_security/_authenticate`` authenticating with the provided API key."""
    headers = {"Authorization": f"ApiKey {params['encoded_api_key']}"}
    if params.get("expect_failure"):
        try:
            await es.perform_request("GET", AUTHENTICATE_PATH, headers=headers)
        except elasticsearch.AuthenticationException:
            return {"weight": 1, "unit": "ops", "credentials": "invalid"}
        raise AssertionError("Authentication with invalid API key credentials unexpectedly succeeded.")
    await es.perform_request("GET", AUTHENTICATE_PATH, headers=headers)
    return 1, "ops"


async def _security_stats_snapshot(es):
    """
    Collects cluster-wide counters that explain the API key authentication path:

    * ``security_crypto_completed``: tasks executed on the ``security-crypto`` thread pool (hash computations that were forked).
    * ``security_index_get_total``: GET requests on the ``.security`` index (API key document cache misses, plus user lookups).
    * ``authenticate_requests``: HTTP requests on ``/_security/_authenticate`` (available since Elasticsearch 8.12).
    * ``process_cpu_millis``: cumulative CPU time of the Elasticsearch process(es).
    """
    snapshot = {
        "security_crypto_completed": 0,
        "security_crypto_rejected": 0,
        "security_crypto_largest": 0,
        "process_cpu_millis": 0,
        "authenticate_requests": 0,
        "security_index_get_total": 0,
        "security_index_get_missing": 0,
        "nodes": 0,
    }
    nodes_stats = await es.nodes.stats(metric=["thread_pool", "process", "http"])
    for node in nodes_stats["nodes"].values():
        snapshot["nodes"] += 1
        crypto = node.get("thread_pool", {}).get(SECURITY_CRYPTO_THREAD_POOL, {})
        snapshot["security_crypto_completed"] += crypto.get("completed", 0)
        snapshot["security_crypto_rejected"] += crypto.get("rejected", 0)
        snapshot["security_crypto_largest"] = max(snapshot["security_crypto_largest"], crypto.get("largest", 0))
        snapshot["process_cpu_millis"] += node.get("process", {}).get("cpu", {}).get("total_in_millis", 0)
        routes = node.get("http", {}).get("routes", {})
        snapshot["authenticate_requests"] += routes.get(AUTHENTICATE_PATH, {}).get("requests", {}).get("count", 0)
    try:
        index_stats = await es.indices.stats(index=".security", metric="get")
        get_stats = index_stats["_all"]["total"]["get"]
        snapshot["security_index_get_total"] = get_stats.get("total", 0)
        snapshot["security_index_get_missing"] = get_stats.get("missing_total", 0)
    except elasticsearch.ApiError as e:
        LOGGER.warning("Could not retrieve stats of the .security index: %s", e)
    return snapshot


async def collect_security_stats(es, params):
    """
    Snapshots security-related server-side counters. With ``phase: before`` the snapshot is persisted; with ``phase: after``
    the deltas to the persisted snapshot are reported in addition (as request meta-data in the metrics store).
    """
    phase = params.get("phase", "after")
    directory = api_keys_dir(params)
    snapshot_file = os.path.join(directory, STATS_SNAPSHOT_FILE)
    snapshot = await _security_stats_snapshot(es)
    snapshot["timestamp"] = time.time()
    result = {"weight": 1, "unit": "ops", **snapshot}
    if phase == "before":
        os.makedirs(directory, exist_ok=True)
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(snapshot, f)
    elif os.path.exists(snapshot_file):
        with open(snapshot_file, "r", encoding="utf-8") as f:
            before = json.load(f)
        for name, value in snapshot.items():
            if isinstance(value, (int, float)) and name in before:
                result[f"{name}_delta"] = value - before[name]
        if result.get("authenticate_requests_delta", 0) > 0:
            result["cpu_micros_per_authenticate"] = result["process_cpu_millis_delta"] * 1000.0 / result["authenticate_requests_delta"]
            result["security_crypto_tasks_per_authenticate"] = (
                result["security_crypto_completed_delta"] / result["authenticate_requests_delta"]
            )
            result["security_index_gets_per_authenticate"] = (
                result["security_index_get_total_delta"] / result["authenticate_requests_delta"]
            )
    else:
        LOGGER.warning("No stats snapshot found at [%s]; reporting absolute values only.", snapshot_file)
    LOGGER.info("Security stats (%s): %s", phase, json.dumps({k: v for k, v in result.items() if k not in ("weight", "unit")}))
    return result


async def cleanup(es, params):
    """Invalidates the API keys of all benchmark users and deletes the users and roles. Intended for persistent clusters."""
    num_users = int(params.get("num_users", 100))
    num_roles = int(params.get("num_roles", 100))

    def invalidate(username):
        return lambda: _with_retries(lambda: es.security.invalidate_api_key(username=username), f"invalidate API keys of {username}")

    def delete_user(username):
        return lambda: _with_retries(lambda: es.options(ignore_status=404).security.delete_user(username=username), f"delete {username}")

    def delete_role(name):
        return lambda: _with_retries(lambda: es.options(ignore_status=404).security.delete_role(name=name), f"delete {name}")

    usernames = [user_name(i) for i in range(num_users)]
    role_names = [role_name(i) for i in range(num_roles)]
    responses = await _gather_in_chunks([invalidate(username) for username in usernames], chunk_size=10)
    invalidated = sum(len(response.get("invalidated_api_keys", [])) for response in responses)
    await _gather_in_chunks([delete_user(username) for username in usernames], chunk_size=25)
    await _gather_in_chunks([delete_role(name) for name in role_names], chunk_size=25)
    LOGGER.info("Invalidated [%d] API keys and deleted [%d] users and [%d] roles.", invalidated, num_users, num_roles)
    return {"weight": 1, "unit": "ops", "invalidated_api_keys": invalidated}


def register(registry):
    registry.register_param_source("api-key-create-param-source", ApiKeyCreateParamSource)
    registry.register_param_source("api-key-authenticate-param-source", ApiKeyAuthenticateParamSource)
    registry.register_runner("create-roles-and-users", create_roles_and_users, async_runner=True)
    registry.register_runner("create-api-keys", create_api_keys, async_runner=True)
    registry.register_runner("authenticate-api-key", authenticate_api_key, async_runner=True)
    registry.register_runner("collect-security-stats", collect_security_stats, async_runner=True)
    registry.register_runner("cleanup", cleanup, async_runner=True)

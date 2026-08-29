import asyncio
import random
import string
import threading


def generate_random_index_expression(length=10):
    base = ''.join(random.choices(string.ascii_lowercase + string.digits + '_-', k=length))
    mode = random.choice(["prefix", "suffix", "both", "none"])

    if mode in ("prefix", "both"):
        base = "*" + base
    if mode in ("suffix", "both"):
        base = base + "*"

    return base


class ApiKeyStore:
    """Thread-safe singleton store for API keys across Rally clients."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.api_keys = []
                    cls._instance.store_lock = threading.Lock()
        return cls._instance

    def add(self, encoded_key):
        with self.store_lock:
            self.api_keys.append(encoded_key)

    def add_batch(self, encoded_keys):
        with self.store_lock:
            self.api_keys.extend(encoded_keys)

    def get_random(self):
        with self.store_lock:
            return random.choice(self.api_keys) if self.api_keys else None

    def count(self):
        with self.store_lock:
            return len(self.api_keys)

    def clear(self):
        with self.store_lock:
            self.api_keys.clear()


class ApiKeyParamSource:
    """Param source that provides random API keys for authentication benchmarking."""

    def __init__(self, track, params, **kwargs):
        self.store = ApiKeyStore()
        self.infinite = True

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        encoded_key = self.store.get_random()
        if not encoded_key:
            raise Exception("No API keys available in store. Ensure create-api-keys ran first.")
        return {"encoded_api_key": encoded_key}


async def create_roles_and_users(es, params):
    """Setup operation: Create 100 roles and 100 users with random role assignments."""
    num_roles = params.get("num_roles", 100)
    num_users = params.get("num_users", 100)
    roles_per_user = params.get("roles_per_user", 2)

    # Create 100 spaces for Kibana application privileges
    spaces = [f"space:space{i}" for i in range(100)]

    # Create roles
    roles = [f"role_{i}" for i in range(num_roles)]

    for role_name in roles:
        indices_privileges = [
            {
                "names": [generate_random_index_expression()],
                "privileges": random.sample(["read", "write", "delete", "create"], k=2)
            }
        ]
        cluster_privileges = random.sample(["all", "monitor", "manage"], k=2)
        selected_spaces = random.sample(spaces, k=1)

        await es.security.put_role(
            name=role_name,
            indices=indices_privileges,
            cluster=cluster_privileges,
            applications=[
                {
                    "application": "kibana-.kibana",
                    "privileges": ["all"],
                    "resources": selected_spaces
                }
            ]
        )

    # Create users with random subset of roles
    for i in range(num_users):
        await es.security.put_user(
            username=f"user_{i}",
            password="password",
            roles=random.sample(roles, k=min(roles_per_user, len(roles)))
        )


async def create_api_keys(es, params):
    """Setup operation: Create API keys using grant API and store encoded values in memory."""
    store = ApiKeyStore()
    store.clear()  # Clear any keys from previous runs

    num_keys = params.get("num_keys", 100000)
    batch_size = params.get("batch_size", 100)
    num_users = params.get("num_users", 100)

    async def create_single_key(key_index):
        user_index = random.randint(0, num_users - 1)
        try:
            response = await es.security.grant_api_key(
                grant_type="password",
                username=f"user_{user_index}",
                password="password",
                api_key={"name": f"api_key_{key_index}", "role_descriptors": {}}
            )
            return response.get('encoded')
        except Exception:
            return None

    # Create keys in batches using asyncio.gather for parallelism
    failed_count = 0
    for batch_start in range(0, num_keys, batch_size):
        batch_end = min(batch_start + batch_size, num_keys)
        tasks = [create_single_key(i) for i in range(batch_start, batch_end)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect successful results
        encoded_keys = [r for r in results if isinstance(r, str)]
        failed_count += len(results) - len(encoded_keys)
        store.add_batch(encoded_keys)

    return {"keys_created": store.count(), "keys_failed": failed_count}


async def authenticate_with_api_key(es, params):
    """Benchmark operation: Authenticate using a random API key."""
    encoded_key = params.get("encoded_api_key")
    if not encoded_key:
        raise Exception("No API key provided in params")

    # Use es.options() to set Authorization header for API key authentication
    await es.options(
        headers={"Authorization": f"ApiKey {encoded_key}"}
    ).security.authenticate()


def register(registry):
    registry.register_runner("create-roles-and-users", create_roles_and_users, async_runner=True)
    registry.register_runner("create-api-keys", create_api_keys, async_runner=True)
    registry.register_runner("authenticate-with-api-key", authenticate_with_api_key, async_runner=True)
    registry.register_param_source("api-key-param-source", ApiKeyParamSource)
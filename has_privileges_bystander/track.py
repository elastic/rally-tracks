import random
import string


def _random_index_expression(wildcard_mode="both"):
    base = "".join(random.choices(string.ascii_lowercase + string.digits + "_-", k=10))
    if wildcard_mode in ("prefix", "both"):
        base = "*" + base
    if wildcard_mode in ("suffix", "both"):
        base = base + "*"
    return base


def build_heavy_has_privileges_body():
    """Build a large, unique _has_privileges request body that forces expensive
    checkPrivileges evaluation on every call.  Each invocation produces a unique
    body so the per-role hasPrivilegesCache always misses."""
    cluster_privs = [
        "monitor",
        "manage",
        "manage_security",
        "manage_pipeline",
        "manage_index_templates",
        "manage_ml",
        "manage_watcher",
        "manage_transform",
        "manage_ccr",
        "manage_ilm",
    ]

    index_privs = []
    for _ in range(50):
        base = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        index_privs.append(
            {
                "names": [f"*{base}*" for _ in range(3)],
                "privileges": random.sample(
                    [
                        "read",
                        "write",
                        "delete",
                        "create",
                        "create_index",
                        "index",
                        "monitor",
                        "manage",
                        "view_index_metadata",
                        "delete_index",
                    ],
                    k=4,
                ),
                "allow_restricted_indices": False,
            }
        )

    return {"cluster": cluster_privs, "index": index_privs}


async def create_roles_and_users(es, params):
    num_roles = params.get("num_roles", 100)
    num_users = params.get("num_users", 1)
    num_roles_per_user = params.get("num_roles_per_user", 100)
    wildcard_mode = params.get("wildcard_mode", "both")
    index_privileges_per_role = params.get("index_privileges_per_role", 10)

    from esrally import exceptions

    if num_roles_per_user > num_roles:
        raise exceptions.InvalidSyntax(f"num_roles_per_user ({num_roles_per_user}) cannot exceed num_roles ({num_roles})")

    roles = [f"role_{i}" for i in range(num_roles)]

    for role_name in roles:
        indices_privileges = [
            {
                "names": [_random_index_expression(wildcard_mode=wildcard_mode)],
                "privileges": random.sample(["read", "write", "delete", "create"], k=2),
            }
            for _ in range(index_privileges_per_role)
        ]
        await es.security.put_role(
            name=role_name,
            indices=indices_privileges,
            cluster=random.sample(["all", "monitor", "manage"], k=2),
        )

    for i in range(num_users):
        await es.security.put_user(
            username=f"user_{i}",
            password="password",
            roles=random.sample(roles, k=num_roles_per_user),
        )

    if params.get("cached_bystander_clients", 0) > 0:
        await es.security.put_role(
            name="bystander_role",
            indices=[{"names": ["test-index"], "privileges": ["read"]}],
            cluster=["monitor"],
        )
        await es.security.put_user(
            username="bystander_user",
            password="password",
            roles=["bystander_role"],
        )


async def has_privileges(es, params):
    num_users = params.get("num_users", 1)
    user_id = random.randint(0, num_users - 1)
    body = build_heavy_has_privileges_body()
    await es.options(
        basic_auth=(f"user_{user_id}", "password"),
    ).security.has_privileges(body=body)


async def has_privileges_cached(es, params):
    await es.options(
        basic_auth=("bystander_user", "password"),
    ).security.has_privileges(body={"cluster": ["monitor"], "index": [{"names": ["test-index"], "privileges": ["read"]}]})


async def cluster_info(es, params):
    await es.info()


def register(registry):
    registry.register_runner("create_roles_and_users", create_roles_and_users, async_runner=True)
    registry.register_runner("has_privileges", has_privileges, async_runner=True)
    registry.register_runner("has_privileges_cached", has_privileges_cached, async_runner=True)
    registry.register_runner("cluster_info", cluster_info, async_runner=True)

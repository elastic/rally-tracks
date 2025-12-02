import bz2
import json
import os
import random
import string

from esrally import exceptions
from jinja2 import Template

from .track_processor import HasPrivilegesDataDownloader


def load_has_privileges_request_body(spaces):
    data_dir = os.path.expanduser("~/.rally/benchmarks/data/has_privileges")
    template_path = os.path.join(data_dir, "has-privileges-request-body.json")

    if not os.path.exists(template_path):
        raise Exception(f"has-privileges-request-body.json not found at {template_path}. Track processor should have downloaded it.")

    with open(template_path, "r") as f:
        template_content = f.read()

    template = Template(template_content)
    rendered = template.render(spaces=spaces)
    return json.loads(rendered)


def generate_random_index_expression(length=10, wildcard_mode="mixed"):
    base = "".join(random.choices(string.ascii_lowercase + string.digits + "_-", k=length))

    if wildcard_mode == "mixed":
        mode = random.choice(["prefix", "suffix", "both"])
    else:
        mode = wildcard_mode

    if mode in ("prefix", "both"):
        base = "*" + base
    if mode in ("suffix", "both"):
        base = base + "*"

    return base


async def create_roles_and_users(es, params):
    # Extract parameters with defaults
    num_roles = params.get("num_roles", 1000)
    num_users = params.get("num_users", 100)
    num_roles_per_user = params.get("num_roles_per_user", 300)
    num_spaces = params.get("num_spaces", 100)
    wildcard_mode = params.get("wildcard_mode", "mixed")

    # Validate parameters
    if num_roles_per_user > num_roles:
        raise exceptions.InvalidSyntax(f"num_roles_per_user ({num_roles_per_user}) cannot exceed num_roles ({num_roles})")

    # create spaces
    spaces = []
    for i in range(num_spaces):
        spaces.append(f"space:space{i}")

    # create roles
    roles = []
    for i in range(num_roles):
        random_role_name = f"role_{i}"
        roles.append(random_role_name)

    for role_name in roles:
        indices_privileges = [
            {
                "names": [generate_random_index_expression(wildcard_mode=wildcard_mode)],
                "privileges": random.sample(["read", "write", "delete", "create"], k=2),
            }
            for _ in range(1)
        ]
        cluster_privileges = random.sample(["all", "monitor", "manage"], k=2)
        selected_spaces = random.sample(spaces, k=1)

        await es.security.put_role(
            name=role_name,
            indices=indices_privileges,
            cluster=cluster_privileges,
            applications=[{"application": "kibana-.kibana", "privileges": ["all"], "resources": selected_spaces}],
        )
    # create users with subset of roles
    for i in range(num_users):
        await es.security.put_user(username="user_" + str(i), password="password", roles=random.sample(roles, k=num_roles_per_user))


async def create_kibana_app_privileges(es, params):
    version = params.get("version")
    filename = f"kibana-app-privileges-{version}.json.bz2"
    data_dir = os.path.expanduser("~/.rally/benchmarks/data/has_privileges")
    data_path = os.path.join(data_dir, filename)

    if not os.path.exists(data_path):
        raise Exception(f"{filename} not found at {data_path}. Track processor should have downloaded it.")

    with bz2.open(data_path, "rt") as kibana_app_privileges_file:
        app_privileges = json.load(kibana_app_privileges_file)
        await es.security.put_privileges(body=app_privileges)


async def has_privileges(es, params):
    # Extract parameters with defaults
    num_users = params.get("num_users", 100)
    num_spaces = params.get("num_spaces", 100)

    # Select a random user (0-indexed, so max is num_users - 1)
    user_id = random.randint(0, num_users - 1)
    spaces = [f"space:space{i}" for i in random.sample(range(num_spaces), k=1)]
    request_body = load_has_privileges_request_body(spaces)
    await es.options(basic_auth=("user_" + str(user_id), "password")).security.has_privileges(body=request_body)


def register(registry):
    registry.register_track_processor(HasPrivilegesDataDownloader())
    registry.register_runner("create_roles_and_users", create_roles_and_users, async_runner=True)
    registry.register_runner("create_kibana_app_privileges", create_kibana_app_privileges, async_runner=True)
    registry.register_runner("has_privileges", has_privileges, async_runner=True)

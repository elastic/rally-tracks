import itertools
import random
import threading
import string
import bz2
import csv
import json
import os

from esrally import exceptions


def generate_random_name(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits + '_-', k=length))

def generate_random_index_expression(length=10):
    base = ''.join(random.choices(string.ascii_lowercase + string.digits + '_-', k=length))
    mode = random.choice(["suffix", "none"])  # include 'none' to exclude adding wildcard

    if mode in ("prefix", "both"):
        base = "*" + base
    if mode in ("suffix", "both"):
        base = base + "*"

    return base

async def create_roles_and_users(es, params):
    # create 100 spaces
    spaces = []
    for i in range(100):
        spaces.append(f"space:space{i}")
    
    # create 100 roles
    roles = []
    for i in range(100):
        random_role_name = f"role_{i}"
        roles.append(random_role_name)

    for role_name in roles:
        indices_privileges = [
            {
                "names": [generate_random_index_expression()],
                "privileges": random.sample(["read", "write", "delete", "create"], k=2)
            } for _ in range(1)
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
    # create 100 users with subset of 2 roles
    for i in range(100):
        await es.security.put_user(
            username="user_" + str(i),
            password="password",
            roles=random.sample(roles, k=2)
        )

async def create_api_keys(es, params):
    # create 100k API keys with random users
    # preserve api key's encoded field so it can be used in authentication step later
    api_keys = []
    for i in range(100000):
        user_index = random.randint(0, 99)
        response = await es.security.create_api_key(
            name=f"api_key_{i}",
            role_descriptors={},
            username=f"user_{user_index}",
            password="password"
        )
        api_keys.append(response['encoded'])
    # store api keys to a file for later use
    api_keys_file = os.path.join(params['track']['params']['data_root'], "api_keys.json")
    with open(api_keys_file, 'w') as f:
        json.dump(api_keys, f)



async def authenticate_api_keys(es, params):    
    # load api keys from file
    api_keys_file = os.path.join(params['track']['params']['data_root'], "api_keys.json")
    with open(api_keys_file, 'r') as f:
        api_keys = json.load(f)
    
    # 10k randomly select an api key and authenticate
    for _ in range(10000):
        random_api_key = random.choice(api_keys)
        await es.security.authenticate(api_key=random_api_key)

def register(registry):
    registry.register_runner("create-roles-and-users", create_roles_and_users, async_runner=True)
    registry.register_runner("create-api-keys", create_api_keys, async_runner=True)
    registry.register_runner("authenticate-api-keys", authenticate_api_keys, async_runner=True)
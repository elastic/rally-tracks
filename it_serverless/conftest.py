# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import collections
import contextlib
import json
import os
import re
import subprocess
import time
import urllib.parse

import pytest
import requests
from elasticsearch import Elasticsearch

BASE_URL = os.environ["RALLY_IT_SERVERLESS_BASE_URL"]
API_KEY = os.environ["RALLY_IT_SERVERLESS_API_KEY"]
GET_CREDENTIALS_ENDPOINT = os.environ["RALLY_IT_SERVERLESS_GET_CREDENTIALS_ENDPOINT"]


ServerlessProjectConfig = collections.namedtuple(
    "ServerlessProjectConfig",
    ["target_host", "username", "password", "api_key"],
)


def serverless_api(method, endpoint, json=None):
    resp = requests.request(
        method,
        BASE_URL + endpoint,
        headers={
            "Authorization": f"ApiKey {API_KEY}",
            "Content-Type": "application/json",
        },
        json=json,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


@pytest.fixture(scope="module")
def serverless_project():
    print("\nCreating project")
    created_project = serverless_api(
        "POST",
        "/api/v1/serverless/projects/elasticsearch",
        json={
            "name": "rally-track-it",
            "region_id": "aws-eu-west-1",
        },
    )

    yield created_project

    print("Deleting project")
    serverless_api("DELETE", f"/api/v1/serverless/projects/elasticsearch/{created_project['id']}")


@pytest.fixture(scope="module")
def serverless_project_config(serverless_project):
    credentials = serverless_api(
        "POST",
        f"/api/v1/serverless/projects/elasticsearch/{serverless_project['id']}{GET_CREDENTIALS_ENDPOINT}",
    )

    es_endpoint = serverless_project["endpoints"]["elasticsearch"]
    es_hostname = urllib.parse.urlparse(es_endpoint).hostname
    rally_target_host = f"{es_hostname}:443"

    print("Waiting for DNS propagation")
    for _ in range(6):
        time.sleep(30)
        with contextlib.suppress(subprocess.CalledProcessError):
            subprocess.run(["nslookup", es_hostname, "8.8.8.8"], check=True)
            break
    else:
        raise ValueError("Timed out waiting for DNS propagation")

    print("Waiting for Elasticsearch")
    for _ in range(18):
        try:
            es = Elasticsearch(
                f"https://{rally_target_host}",
                basic_auth=(
                    credentials["username"],
                    credentials["password"],
                ),
                request_timeout=10,
            )
            info = es.info()
            print("GET /")
            print(json.dumps(info.body, indent=2))

            authenticate = es.perform_request(method="GET", path="/_security/_authenticate")
            print("GET /_security/_authenticate")
            print(json.dumps(authenticate.body, indent=2))

            break
        except Exception as e:
            print(f"GET / Failed with {type(e)}")
            time.sleep(10)
    else:
        raise ValueError("Timed out waiting for Elasticsearch")

    # Create API key to test Rally with a public user
    for _ in range(3):
        try:
            api_key = es.security.create_api_key(name="public-api-key")
            break
        except Exception as e:
            print(f"API create failed with {type(e)}")
            time.sleep(10)
    else:
        raise ValueError("Timed out waiting for API key")

    yield ServerlessProjectConfig(
        rally_target_host,
        credentials["username"],
        credentials["password"],
        api_key.body["encoded"],
    )


def client_options(client_auth):
    return {
        "default": {
            "verify_certs": False,
            "use_ssl": True,
            "timeout": 240,
            **client_auth,
        }
    }


def write_options_file(config: ServerlessProjectConfig, operator, tmp_path):
    if operator:
        client_auth = {
            "basic_auth_user": config.username,
            "basic_auth_password": config.password,
        }
    else:
        client_auth = {"api_key": config.api_key}

    options_file = tmp_path / "client-options.json"
    with options_file.open("w") as f:
        json.dump(client_options(client_auth), fp=f)
    return options_file
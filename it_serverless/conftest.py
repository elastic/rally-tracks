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

import contextlib
import json
import os
import subprocess
import time
import urllib.parse
from dataclasses import dataclass

import pytest
import requests
from elasticsearch import Elasticsearch

BASE_URL = os.environ["RALLY_IT_SERVERLESS_BASE_URL"]
API_KEY = os.environ["RALLY_IT_SERVERLESS_API_KEY"]
GET_CREDENTIALS_ENDPOINT = os.environ["RALLY_IT_SERVERLESS_GET_CREDENTIALS_ENDPOINT"]
PIPELINE_NAME = os.environ.get("BUILDKITE_PIPELINE_SLUG")
BUILD_NUMBER = os.environ.get("BUILDKITE_BUILD_NUMBER")


@dataclass
class ServerlessProjectConfig:
    target_host: str
    username: str
    password: str
    api_key: str
    user_client_options_file: str = None
    operator_client_options_file: str = None

    def get_client_options_file(self, operator) -> str:
        return self.operator_client_options_file if operator else self.user_client_options_file

    @staticmethod
    def _client_options(client_auth):
        return {
            "default": {
                "verify_certs": False,
                "use_ssl": True,
                "timeout": 240,
                **client_auth,
            }
        }

    def prepare_client_options_files(self, tmpdir_factory):
        tmp_path = tmpdir_factory.mktemp("client-options")

        client_auth = {
            "basic_auth_user": self.username,
            "basic_auth_password": self.password,
        }
        self.operator_client_options_file = tmp_path / "operator.json"
        with self.operator_client_options_file.open("w") as f:
            json.dump(self._client_options(client_auth), fp=f)

        client_auth = {"api_key": self.api_key}
        self.user_client_options_file = tmp_path / "user.json"
        with self.user_client_options_file.open("w") as f:
            json.dump(self._client_options(client_auth), fp=f)


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
def project():
    print("\nCreating project")
    project_name = "rally-track-it"
    if PIPELINE_NAME is not None and BUILD_NUMBER is not None:
        project_name = f"{PIPELINE_NAME}-{BUILD_NUMBER}"
    created_project = serverless_api(
        "POST",
        "/api/v1/serverless/projects/elasticsearch",
        json={
            "name": project_name,
            "region_id": "aws-eu-west-1",
        },
    )

    yield created_project

    print("Deleting project")
    serverless_api("DELETE", f"/api/v1/serverless/projects/elasticsearch/{created_project['id']}")


@pytest.fixture(scope="module")
def project_config(project, tmpdir_factory):
    credentials = serverless_api(
        "POST",
        f"/api/v1/serverless/projects/elasticsearch/{project['id']}{GET_CREDENTIALS_ENDPOINT}",
    )

    es_endpoint = project["endpoints"]["elasticsearch"]
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
            print(f"GET / Failed with {str(e)}")
            time.sleep(10)
    else:
        raise ValueError("Timed out waiting for Elasticsearch")

    # Create API key to test Rally with a public user privileges
    print("Waiting for API key")
    for _ in range(18):
        try:
            api_key = es.security.create_api_key(name="public-api-key")
            break
        except Exception as e:
            print(f"API create failed with {str(e)}")
            time.sleep(10)
    else:
        raise ValueError("Timed out waiting for API key")

    # Confirm API key is working fine
    print("Testing API key")
    for _ in range(18):
        try:
            es = Elasticsearch(
                f"https://{rally_target_host}",
                api_key=api_key.body["encoded"],
                request_timeout=10,
            )
            info = es.info()
            break
        except Exception as e:
            print(f"API verification failed with {str(e)}")
            time.sleep(10)
    else:
        raise ValueError("Timed out verifying API key")

    project_config = ServerlessProjectConfig(
        rally_target_host,
        credentials["username"],
        credentials["password"],
        api_key.body["encoded"],
    )
    project_config.prepare_client_options_files(tmpdir_factory)
    yield project_config


def pytest_addoption(parser):
    parser.addoption("--operator", action="store_true", help="run as operator")


def pytest_generate_tests(metafunc):
    if "operator" in metafunc.fixturenames:
        operator = metafunc.config.getoption("operator")
        label = "operator" if operator else "user"
        metafunc.parametrize("operator", [operator], ids=[label])


def pytest_configure(config):
    config.addinivalue_line("markers", "operator_only: mark test for operator only")


def pytest_collection_modifyitems(config, items):
    skip = pytest.mark.skip()
    for item in items:
        if not config.getoption("operator") and "operator_only" in item.keywords:
            item.add_marker(skip)

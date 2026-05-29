# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from urllib.parse import urlparse

from esrally.client import EsClientFactory


def create_rally_elasticsearch_client(
    url: str,
    *,
    basic_auth: tuple[str, str] | None = None,
    api_key: str | None = None,
    request_timeout: int | None = None,
    verify_certs: bool | None = None,
    distribution_version: str | None = None,
    distribution_flavor: str | None = None,
):
    parsed_url = urlparse(url)
    if parsed_url.scheme not in ("http", "https") or parsed_url.hostname is None:
        raise ValueError(f"Expected an http(s) Elasticsearch URL, but got [{url}]")

    host = {
        "host": parsed_url.hostname,
        "port": parsed_url.port or (443 if parsed_url.scheme == "https" else 80),
    }
    if parsed_url.path and parsed_url.path != "/":
        host["url_prefix"] = parsed_url.path.rstrip("/")

    client_options = {}
    if parsed_url.scheme == "https":
        client_options["use_ssl"] = True
    if basic_auth is not None:
        client_options["basic_auth_user"], client_options["basic_auth_password"] = basic_auth
    if api_key is not None:
        client_options["api_key"] = api_key
    if request_timeout is not None:
        client_options["request_timeout"] = request_timeout
    if verify_certs is not None:
        client_options["verify_certs"] = verify_certs

    return EsClientFactory(
        [host],
        client_options,
        distribution_version=distribution_version,
        distribution_flavor=distribution_flavor,
    ).create()

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

import os
import json
import logging

from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def load_index_template(track, asset_content):
    pass


def load_component_template(track, asset_content):
    pass


def load_ingest_pipeline(track, asset_content):
    pass


def load_ilm_policy(track, asset_content):
    pass


asset_loaders = {
    "component_templates": load_component_template,
    "index_templates": load_index_template,
    "ingest_pipelines": load_ingest_pipeline,
    "ilm_policies": load_ilm_policy,
}


def load_from_github(track, packages, repo_path):
    from elastic.package import assets
    from github import Github

    if packages:
        github = Github(os.getenv("ASSETS_AUTH_TOKEN") or None)
        repo = github.get_repo(repo_path)

    for package in packages:
        logger.info(f"Downloading assets of [{package}] from [{repo.html_url}]")
        entries = assets.get_remote_assets(package, repo)

        count = 0
        for path, content in assets.download_assets(entries):
            path_parts = os.path.split(path[len(package) + 1:])

            if not path_parts[0]:
                continue
            if path_parts[0] in asset_loaders:
                asset_loaders[path_parts[0]](track, json.loads(content))
                count += 1
            else:
                logger.warning(f"Skipping unknown asset type: {path_parts[0]}")

        logger.info(f"Loaded [{count}] assets")


class AssetsLoader:
    def on_after_load_track(self, track):

        params = track.selected_challenge_or_default.parameters.get("assets", {})
        repository = params.get("repository", "https://github.com/elastic/package-assets")
        packages = params.get("packages", [])

        repo_parts = urlparse(repository)
        if repo_parts.scheme.startswith("http") and repo_parts.netloc == "github.com":
            load_from_github(track, packages, repo_parts.path[1:])
        else:
            raise ValueError(f"Unsupported repository: {repository}")

    def on_prepare_track(self, track, data_root_dir):
        return []

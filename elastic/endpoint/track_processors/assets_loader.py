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
import shutil
import logging

from urllib.parse import urlparse

from esrally.track import (
    Index,
    IndexTemplate,
    ComponentTemplate,
)

logger = logging.getLogger(__name__)


def load_index_template(track, asset_content, kibana_space="default"):
    index_name = asset_content["name"]

    track.composable_templates += [
        IndexTemplate(
            index_name,
            index_pattern,
            asset_content,
        )
        for index_pattern in asset_content["index_template"]["index_patterns"]
    ]
    track.data_streams.append(Index(f"{index_name}-{kibana_space}"))


def load_component_template(track, asset_content):
    track.component_templates.append(
        ComponentTemplate(
            asset_content["name"],
            asset_content["component_template"],
        )
    )


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


def download_from_github(track, packages, repo_path, assets_root):
    from elastic.package import assets
    from github import Github

    if not packages:
        raise ValueError("Required param 'packages' is empty or not configured")

    github = Github(os.getenv("ASSETS_AUTH_TOKEN") or None)
    repo = github.get_repo(repo_path)

    for package in packages:
        logger.info(f"Downloading assets of [{package}] from [{repo.html_url}]")
        entries = assets.get_remote_assets(package, repo)

        dest_package_path = os.path.join(assets_root, package)
        if os.path.exists(dest_package_path):
            shutil.rmtree(dest_package_path)

        count = 0
        for path, content in assets.download_assets(entries):
            asset_path = os.path.join(assets_root, path)
            os.makedirs(os.path.dirname(asset_path), exist_ok=True)
            with open(asset_path, "wb") as f:
                f.write(content)

            path_parts = os.path.split(path[len(package) + 1:])
            if not path_parts[0]:
                continue
            if path_parts[0] in asset_loaders:
                asset_loaders[path_parts[0]](track, json.loads(content))
                count += 1

        logger.info(f"Loaded [{count}] assets")


def load_from_path(track, packages, path):
    from elastic.package import assets

    if not packages:
        raise ValueError("Required param 'packages' is empty or not configured")

    for package in packages:
        logger.info(f"Loading assets of [{package}] from [{path}]")

        count = 0
        for path, content in assets.get_local_assets(package, path):
            path_parts = os.path.split(path[len(package) + 1:])
            if not path_parts[0]:
                continue
            if path_parts[0] in asset_loaders:
                asset_loaders[path_parts[0]](track, json.loads(content))
                count += 1

        logger.info(f"Loaded [{count}] assets")


class AssetsLoader:
    def on_after_load_track(self, track):
        try:
            from elastic.package import assets  # noqa: F401
        except ModuleNotFoundError:
            logger.warning("Cannot import module [elastic.package.assets], assets are not loaded")
            return

        asset_groups = track.selected_challenge_or_default.parameters.get("assets", [])

        for assets_group in asset_groups:
            repository = assets_group.get("repository", "https://github.com/elastic/package-assets")
            packages = assets_group.get("packages", [])

            repo_parts = urlparse(repository)
            if repo_parts.scheme.startswith("http") and repo_parts.netloc == "github.com":
                assets_root = os.path.join(track.root, "assets", repo_parts.path[1:])
                download_from_github(track, packages, repo_parts.path[1:], assets_root)
            elif repo_parts.scheme == "file":
                if repo_parts.netloc == '.':
                    assets_root = os.path.join(track.root, "." + repo_parts.path)
                else:
                    assets_root = repo_parts.path
                load_from_path(track, packages, assets_root)
            else:
                raise ValueError(f"Unsupported repository: {repository}")

            assets_group["path"] = os.path.abspath(assets_root)
            logger.info(f"Assets group path is [{assets_group['path']}]")

    def on_prepare_track(self, track, data_root_dir):
        return []

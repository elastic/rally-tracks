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

import json
import logging
import os
import shutil
from urllib.parse import urlparse

from esrally.track import ComponentTemplate, Index, IndexTemplate

from esrally.utils import git

RALLY_HOME = os.getenv("RALLY_HOME", os.path.expanduser("~"))
RALLY_CONFIG_DIR = os.path.join(RALLY_HOME, ".rally")
RALLY_ASSETS_DIR = os.path.join(RALLY_CONFIG_DIR, "benchmarks", "assets")

logger = logging.getLogger(__name__)


def load_index_template(track, asset_content, kibana_space="default"):
    index_name = asset_content.pop("name")
    index_template = asset_content.pop("index_template")
    index_patterns = index_template["index_patterns"]

    track.composable_templates.append(
        IndexTemplate(
            index_name,
            index_patterns,
            index_template,
        )
    )

    track.data_streams.append(Index(f"{index_name}-{kibana_space}"))


def load_component_template(track, asset_content):
    track.component_templates.append(
        ComponentTemplate(
            asset_content["name"],
            asset_content["component_template"],
        )
    )

def load_composable_template(track, asset_content):
    pass


def load_ingest_pipeline(track, asset_content):
    pass


def load_ilm_policy(track, asset_content):
    pass


asset_loaders = {
    "composable_templates": load_composable_template,
    "component_templates": load_component_template,
    "index_templates": load_index_template,
    "ingest_pipelines": load_ingest_pipeline,
    "ilm_policies": load_ilm_policy,
}


def clone_repo(repo_path, assets_root, branch):
    if os.path.isdir(assets_root):
        logger.info(f"Directory [{assets_root}] already exists. Skipping clone.")
        git.checkout(assets_root, branch=branch)
    else:
        logger.info(f"Cloning [{repo_path}] into [{assets_root}]")
        git.clone(src=assets_root, remote=repo_path)
        logger.info(f"Checking out branch [{branch}] in [{assets_root}]")
        git.checkout(assets_root, branch=branch)


def load_from_path(track, packages, path):
    try:
        from elastic.package import assets  # noqa: F401
    except ModuleNotFoundError:
        logger.warning("Cannot import module [elastic.package.assets], assets are not loaded")
        return

    if not packages:
        raise ValueError("Required param 'packages' is empty or not configured")

    for package in packages:
        logger.info(f"Loading assets of [{package}] from [{path}]")

        count = 0
        for asset_path, content in assets.get_local_assets(package, path):
            (asset_type, _) = os.path.split(asset_path[len(package) + 1 :])
            asset_loader = asset_loaders.get(asset_type)
            if asset_loader is not None:
                logger.info(f"Loading [{asset_path}]")
                asset_loader(track, json.loads(content))
                count += 1
            else:
                continue

        logger.info(f"Loaded [{count}] assets")


class AssetsLoader:
    def on_after_load_track(self, track):
        asset_groups = track.selected_challenge_or_default.parameters.get("assets", [])

        for assets_group in asset_groups:
            repository = assets_group.get("repository", "https://github.com/elastic/package-assets")
            branch = assets_group.get("branch", "production")
            packages = assets_group.get("packages", [])

            repo_parts = urlparse(repository)
            if repo_parts.scheme.startswith("http"):
                assets_root = os.path.join(RALLY_ASSETS_DIR, repo_parts.path[1:])
                clone_repo(repository, assets_root, branch)
            elif repo_parts.scheme == "file":
                if repo_parts.netloc == ".":
                    assets_root = os.path.join(track.root, "." + repo_parts.path)
                else:
                    assets_root = repo_parts.path
            else:
                raise ValueError(f"Unsupported repository: {repository}")

            load_from_path(track, packages, assets_root)
            assets_group["path"] = os.path.abspath(assets_root)
            logger.info(f"Assets group path is [{assets_group['path']}]")

    def on_prepare_track(self, track, data_root_dir):
        return []

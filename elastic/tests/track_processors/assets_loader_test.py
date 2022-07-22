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

import pytest

from endpoint.track_processors.assets_loader import AssetsLoader
from tests.parameter_sources import EmptyTrack


@pytest.fixture
def assets_loader():
    return AssetsLoader()


@pytest.fixture
def parameters():
    return {
        "assets": {
            "repository": "file://./tests/track_processors/resources/assets",
            "packages": [
                "endpoint/8.3.0"
            ]
        }
    }


@pytest.fixture
def track(parameters, assets_loader):
    track = EmptyTrack(parameters=parameters)
    assets_loader.on_after_load_track(track)
    return track


def test_no_assets(assets_loader):
    track = EmptyTrack()
    assets_loader.on_after_load_track(track)

    assert track.data_streams == []
    assert track.component_templates == []
    assert track.composable_templates == []


def test_empty_assets(assets_loader):
    parameters = {
        "assets": {
        }
    }
    track = EmptyTrack(parameters=parameters)
    assets_loader.on_after_load_track(track)

    assert track.data_streams == []
    assert track.component_templates == []
    assert track.composable_templates == []


def test_empty_packages(assets_loader):
    parameters = {
        "assets": {
            "packages": [
            ]
        }
    }
    track = EmptyTrack(parameters=parameters)
    assets_loader.on_after_load_track(track)

    assert track.data_streams == []
    assert track.component_templates == []
    assert track.composable_templates == []


def test_invalid_packages(assets_loader):
    parameters = {
        "assets": {
            "repository": "file://./tests/track_processors/resources/assets",
            "packages": [
                "invalid/a.b.c"
            ]
        }
    }
    track = EmptyTrack(parameters=parameters)
    with pytest.raises(ValueError) as exc:
        assets_loader.on_after_load_track(track)
    assert str(exc.value) == f"Package not found: {parameters['assets']['packages'][0]}"


def test_invalid_repo(assets_loader):
    for repo in ["git@github.com:elastic/package-assets", "https://gitlab.com/elastic/package-assets"]:
        parameters = {
            "assets": {
                "repository": repo
            }
        }
        track = EmptyTrack(parameters=parameters)

        with pytest.raises(ValueError) as exc:
            assets_loader.on_after_load_track(track)
        assert str(exc.value) == f"Unsupported repository: {repo}"

        assert track.data_streams == []
        assert track.component_templates == []
        assert track.composable_templates == []


def test_data_stream_names(assets_loader, track):
    data_stream_names = sorted(ds.name for ds in track.data_streams)
    assert data_stream_names == [
        ".logs-endpoint.action.responses-default",
        ".logs-endpoint.actions-default",
        ".logs-endpoint.diagnostic.collection-default",
        "logs-endpoint.alerts-default",
        "logs-endpoint.events.file-default",
        "logs-endpoint.events.library-default",
        "logs-endpoint.events.network-default",
        "logs-endpoint.events.process-default",
        "logs-endpoint.events.registry-default",
        "logs-endpoint.events.security-default",
        "metrics-endpoint.metadata-default",
        "metrics-endpoint.metrics-default",
        "metrics-endpoint.policy-default",
    ]


def test_composable_templates(assets_loader, track):
    composable_template_names = sorted(ct.name for ct in track.composable_templates)
    assert composable_template_names == [
        ".logs-endpoint.action.responses",
        ".logs-endpoint.actions",
        ".logs-endpoint.diagnostic.collection",
        "logs-endpoint.alerts",
        "logs-endpoint.events.file",
        "logs-endpoint.events.library",
        "logs-endpoint.events.network",
        "logs-endpoint.events.process",
        "logs-endpoint.events.registry",
        "logs-endpoint.events.security",
        "metrics-endpoint.metadata",
        "metrics-endpoint.metrics",
        "metrics-endpoint.policy",
    ]

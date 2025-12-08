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

import pytest

from .conftest import ServerlessProjectConfig

pytest_rally = pytest.importorskip("pytest_rally")

BASE_PARAMS = {
    "start_date": "2021-01-01T00-00-00Z",
    "end_date": "2021-01-01T00-01-00Z",
    "max_total_download_gb": "18",
    "raw_data_volume_per_day": "72GB",
    "max_generated_corpus_size": "1GB",
    "wait_for_status": "green",
    "force_data_generation": "true",
    "number_of_shards": "2",
    "number_of_replicas": "1",
}


def params(updates=None):
    base = BASE_PARAMS.copy()
    if updates is None:
        return base
    else:
        return {**base, **updates}


@pytest.mark.track("elastic/logs")
@pytest.mark.operator_only
class TestLogs:
    def test_logs_fails_if_assets_not_installed(self, operator, rally, capsys, project_config: ServerlessProjectConfig):
        ret = rally.race(
            track="elastic/logs",
            exclude_tasks="tag:setup",
            client_options=project_config.get_client_options_file(operator),
            target_hosts=project_config.target_host,
        )
        message = "Index templates missing for packages: ['apache', 'kafka', 'mysql', 'nginx', 'postgresql', 'redis', 'system']"
        stdout = capsys.readouterr().out
        assert message in stdout
        assert ret != 0

    def test_logs_default(self, operator, rally, project_config: ServerlessProjectConfig):
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing",
            track_params="number_of_replicas:1",
            client_options=project_config.get_client_options_file(operator),
            target_hosts=project_config.target_host,
        )
        assert ret == 0

    def test_logs_disk_usage(self, operator, rally, project_config: ServerlessProjectConfig):
        # <index>/_stats not available for public user
        if not operator:
            pytest.skip()
        custom = {"number_of_shards": 4}
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-disk-usage",
            track_params=params(updates=custom),
            client_options=project_config.get_client_options_file(operator),
            target_hosts=project_config.target_host,
        )
        assert ret == 0

    def test_logs_indexing_unthrottled(self, operator, rally, project_config: ServerlessProjectConfig):
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing",
            track_params=params(),
            client_options=project_config.get_client_options_file(operator),
            target_hosts=project_config.target_host,
        )
        assert ret == 0

    def test_logs_querying(self, operator, rally, project_config: ServerlessProjectConfig):
        custom = {
            "query_warmup_time_period": "1",
            "query_time_period": "1",
            "workflow_time_interval": "1",
            "think_time_interval": "1",
        }
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-querying",
            track_params=params(updates=custom),
            exclude_tasks="tag:setup",
            client_options=project_config.get_client_options_file(operator),
            target_hosts=project_config.target_host,
        )
        assert ret == 0

    def test_logs_indexing_querying_unthrottled(self, operator, rally, project_config: ServerlessProjectConfig):
        custom = {
            "query_warmup_time_period": "1",
            "query_time_period": "1",
            "workflow_time_interval": "1",
            "think_time_interval": "1",
        }
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing-querying",
            track_params=params(updates=custom),
            exclude_tasks="tag:setup",
            client_options=project_config.get_client_options_file(operator),
            target_hosts=project_config.target_host,
        )
        assert ret == 0

    def test_logs_indexing_throttled(self, operator, rally, project_config: ServerlessProjectConfig):
        custom = {"throttle_indexing": "true"}
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing",
            track_params=params(updates=custom),
            client_options=project_config.get_client_options_file(operator),
            target_hosts=project_config.target_host,
        )
        assert ret == 0

    def test_logs_indexing_querying_throttled(self, operator, rally, project_config: ServerlessProjectConfig):
        custom = {
            "query_warmup_time_period": "1",
            "query_time_period": "1",
            "workflow_time_interval": "1",
            "think_time_interval": "1",
            "throttle_indexing": "true",
        }
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing-querying",
            track_params=params(updates=custom),
            exclude_tasks="tag:setup",
            client_options=project_config.get_client_options_file(operator),
            target_hosts=project_config.target_host,
        )
        assert ret == 0

    def test_logs_querying_with_preloaded_data(self, operator, rally, project_config: ServerlessProjectConfig):
        custom = {
            "bulk_start_date": "2020-09-30T00-00-00Z",
            "bulk_end_date": "2020-09-30T00-01-00Z",
            "query_warmup_time_period": "1",
            "query_time_period": "1",
            "workflow_time_interval": "1",
            "think_time_interval": "1",
        }
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-querying",
            track_params=params(updates=custom),
            client_options=project_config.get_client_options_file(operator),
            target_hosts=project_config.target_host,
        )
        assert ret == 0

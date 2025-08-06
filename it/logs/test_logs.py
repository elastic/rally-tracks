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

from it.logs import BASE_PARAMS, params

pytest_rally = pytest.importorskip("pytest_rally")


class TestLogs:
    def test_logs_fails_if_assets_not_installed(self, es_cluster, rally, capsys):
        ret = rally.race(track="elastic/logs", exclude_tasks="tag:setup")
        message = "Index templates missing for packages: ['apache', 'kafka', 'mysql', 'nginx', 'postgresql', 'redis', 'system']"
        stdout = capsys.readouterr().out
        assert message in stdout
        assert ret != 0

    def test_logs_default(self, es_cluster, rally):
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing",
            track_params="number_of_replicas:0",
        )
        assert ret == 0

    def test_logs_streams(self, es_cluster, rally):
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-streams",
            track_params=params(),
        )
        assert ret == 0

    def test_logs_disable_pipelines(self, es_cluster, rally):
        custom = {"number_of_replicas": 0, "disable_pipelines": "true"}
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing",
            track_params=params(updates=custom),
        )
        assert ret == 0

    def test_logs_disk_usage(self, es_cluster, rally):
        custom = {"number_of_shards": 4}
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-disk-usage",
            track_params=params(updates=custom),
        )
        assert ret == 0

    def test_logs_indexing_unthrottled(self, es_cluster, rally):
        ret = rally.race(track="elastic/logs", challenge="logging-indexing", track_params=params())
        assert ret == 0

    def test_logs_querying(self, rally, es_cluster):
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
        )
        assert ret == 0

    def test_logs_indexing_querying_unthrottled(self, es_cluster, rally):
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
        )
        assert ret == 0

    def test_logs_indexing_throttled(self, es_cluster, rally):
        custom = {"throttle_indexing": "true"}
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing",
            track_params=params(updates=custom),
        )
        assert ret == 0

    def test_logs_indexing_querying_throttled(self, es_cluster, rally):
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
        )
        assert ret == 0

    def test_logs_querying_with_preloaded_data(self, es_cluster, rally):
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
        )
        assert ret == 0

    def test_logs_many_shards_quantitative(self, es_cluster, rally):
        custom = {"number_of_shards": 4}
        ret = rally.race(
            track="elastic/logs",
            challenge="many-shards-quantitative",
            track_params=params(updates=custom),
        )
        assert ret == 0

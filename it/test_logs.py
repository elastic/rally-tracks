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

pytest_rally = pytest.importorskip("pytest_rally")

BASE_PARAMS = {
    "start_date": "2021-01-01T00-00-00Z",
    "end_date": "2021-01-01T00-00-02Z",
    "max_total_download_gb": "18",
    "raw_data_volume_per_day": "72GB",
    "max_generated_corpus_size": "1GB",
    "wait_for_status": "green",
    "force_data_generation": "true",
    "number_of_shards": "2",
    "number_of_replicas": "0",
}

def params(updates=None):
    base = BASE_PARAMS.copy()
    if updates is None:
        return base
    else:
        return {**base, **updates}

class TestLogs:
    def test_logs_default(self, es_cluster, rally):
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing",
            track_params="number_of_replicas:0"
        )
        assert ret == 0

    def test_logs_disk_usage(self, es_cluster, rally):
        custom = {'number_of_shards': 4}
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-disk-usage",
            track_params=params(updates=custom)
        )
        assert ret == 0

    def test_logs_indexing_unthrottled(self, es_cluster, rally):
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing",
            track_params=params()
        )
        assert ret == 0

    def test_logs_querying(self, rally, es_cluster):
        custom = {'query_warmup_time_period': '30', 'query_time_period': '60'}
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-querying",
            track_params=params(updates=custom),
            exclude_tasks="tag:setup"
        )
        assert ret == 0

    def test_logs_indexing_querying_unthrottled(self, es_cluster, rally):
        custom = {
            'query_warmup_time_period': '30',
            'query_time_period': '60'
        }
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing-querying",
            track_params=params(updates=custom),
            exclude_tasks="tag:setup"
        )
        assert ret == 0

    def test_logs_indexing_throttled(self, es_cluster, rally):
        custom = {'throttle_indexing': 'true'}
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing",
            track_params=params(updates=custom)
        )
        assert ret == 0

    def test_logs_indexing_querying_throttled(self, es_cluster, rally):
        custom = {
            'query_warmup_time_period': '30',
            'query_time_period': '60',
            'throttle_indexing': 'true'
        }
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-indexing-querying",
            track_params=params(updates=custom),
            exclude_tasks="tag:setup"
        )
        assert ret == 0

    def test_logs_querying_with_preloaded_data(self, es_cluster, rally):
        custom = {
            'bulk_start_date': '2020-09-30T00-00-00Z',
            'bulk_end_date': '2020-09-30T00-00-02Z',
            'query_warmup_time_period': '30',
            'query_time_period': '60'
        }
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-querying",
            track_params=params(updates=custom)
        )
        assert ret == 0

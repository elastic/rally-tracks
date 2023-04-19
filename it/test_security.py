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


class TestSecurity:
    def test_security_indexing(self, es_cluster, rally):
        ret = rally.race(track="elastic/security", challenge="security-indexing", track_params={"number_of_replicas": "0"})
        assert ret == 0

    def test_security_indexing_querying(self, es_cluster, rally):
        ret = rally.race(
            track="elastic/security",
            challenge="security-indexing-querying",
            track_params={
                "number_of_replicas": "0",
                "query_warmup_time_period": "1",
                "query_time_period": "1",
                "workflow_time_interval": "1",
                "think_time_interval": "1",
            },
        )
        assert ret == 0

    def test_security_generate_alerts_source_events(self, es_cluster, rally):
        ret = rally.race(track="elastic/security", challenge="generate-alerts-source-events", track_params={"number_of_replicas": "0"})
        assert ret == 0

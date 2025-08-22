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


class TestLogsUnmapped:
    def test_logs_chicken(self, es_cluster, rally):
        custom = {"mapping": "unmapped"}
        ret = rally.race(
            track="elastic/logs",
            challenge="logging-insist-chicken",
            track_params=params(updates=custom),
        )
        assert ret == 0

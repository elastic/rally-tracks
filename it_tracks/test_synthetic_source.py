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
    "source_mode": "synthetic",
    "number_of_replicas": "0",
}


def params(updates=None):
    base = BASE_PARAMS.copy()
    if updates is None:
        return base
    else:
        return {**base, **updates}


class TestSyntheticSource:
    @pytest.mark.track("tsdb")
    def test_tsdb_default(self, es_cluster, rally):
        ret = rally.race(
            track="tsdb",
            track_params=params(),
        )
        assert ret == 0

    @pytest.mark.track("nyc_taxis")
    def test_nyc_taxis_default(self, es_cluster, rally):
        ret = rally.race(
            track="nyc_taxis",
            track_params=params(),
        )

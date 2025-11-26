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
pytestmark = pytest.mark.es_cluster_car("4gheap,trial-license,x-pack-security,lean-watermarks")


@pytest.mark.track("has_privileges")
class TestHasPrivileges:
    def test_has_privileges_default(self, es_cluster, rally):
        ret = rally.race(
            track="has_privileges",
            challenge="default",
            client_options="use_ssl:true,verify_certs:false,basic_auth_user:'rally',basic_auth_password:'rally-password'",
            enable_assertions=False,
        )
        assert ret == 0

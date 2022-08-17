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

import copy
from unittest import mock
import pytest
from shared.runners.remote_cluster import ConfigureRemoteCluster, FollowIndexRunner
from tests import as_future


class TestConfigureRemoteCluster:

    @pytest.fixture
    @mock.patch("elasticsearch.Elasticsearch")
    def setup_es(self, es):
        remote_es = es
        local_es = copy.deepcopy(es)

        multi_es = {
            "remote-cluster": remote_es,
            "local-cluster": local_es,
        }
        return multi_es

    @pytest.fixture
    def setup_params(self):
        params = {
            "remote-cluster": "remote-cluster",
            "local-cluster": "local-cluster"
        }
        return params

    @pytest.mark.asyncio
    async def test_configure_remote_cluster(self, setup_es, setup_params):

        setup_es["remote-cluster"].nodes.info.return_value = as_future(
            {
                "cluster_name": "remote_test_cluster",
                "nodes": {
                    "ZrKjLJ1cT6eXblbjwMkkFA": {
                        "transport_address": "127.0.0.1:39320",
                    },
                    "ZrKjLJ1cT6eXblbjwMkkFb": {
                        "transport_address": "127.0.0.2:39320",
                    }
                }
            }
        )

        setup_es["local-cluster"].cluster.put_settings.return_value = as_future({})
        setup_es["local-cluster"].cluster.remote_info.return_value = as_future(
            {
                "remote_test_cluster": {
                    "connected": True,
                    "mode": "sniff",
                    "seeds": ["127.0.0.1:39320"],
                    "num_nodes_connected": 1,
                    "max_connections_per_cluster": 3,
                    "initial_connect_timeout": "30s",
                    "skip_unavailable": False
                }
            }
        )

        cfg_remote_cluster = ConfigureRemoteCluster()
        await cfg_remote_cluster(setup_es, setup_params)

        setup_es["local-cluster"].cluster.put_settings.assert_called_with(
            body={"persistent": {
                    "cluster.remote.remote_test_cluster.seeds": ["127.0.0.1:39320", "127.0.0.2:39320"]
                }
            }
        )

    @pytest.mark.asyncio
    async def test_configure_remote_cluster_not_connected(self, setup_es, setup_params):

        setup_es["remote-cluster"].nodes.info.return_value = as_future(
            {
                "cluster_name": "remote_test_cluster",
                "nodes": {
                    "ZrKjLJ1cT6eXblbjwMkkFA": {
                    "transport_address": "127.0.0.1:39320",
                    },
                    "ZrKjLJ1cT6eXblbjwMkkFB": {
                    "transport_address": "127.0.0.2:39320",
                    }
                }
            }
        )

        setup_es["local-cluster"].cluster.put_settings.return_value = as_future({})
        setup_es["local-cluster"].cluster.remote_info.return_value = as_future(
            {
                "remote_test_cluster": {
                    "connected": False,
                    "mode": "sniff",
                    "seeds": ["127.0.0.1:39320"],
                    "num_nodes_connected": 1,
                    "max_connections_per_cluster": 3,
                    "initial_connect_timeout": "30s",
                    "skip_unavailable": False
                }
            }
        )

        cfg_remote_cluster = ConfigureRemoteCluster()
        with pytest.raises(BaseException) as e:
            await cfg_remote_cluster(setup_es, setup_params)

        assert(
            "Unable to connect [local-cluster] to cluster [remote_test_cluster]. Check each cluster's "
            "logs for more information on why the connection failed." in str(e)
        )


class TestFollowIndexRunner:

    @pytest.fixture
    @mock.patch("elasticsearch.Elasticsearch")
    def setup_es(self, es):
        remote_es = es
        local_es = copy.deepcopy(es)

        multi_es = {
            "remote-cluster": remote_es,
            "local-cluster": local_es,
        }
        return multi_es

    @pytest.fixture
    def setup_params(self):
        params = {
            "remote-cluster": "remote-cluster",
            "local-cluster": "local-cluster",
            "index": "logs-*"
        }
        return params

    @pytest.mark.asyncio
    async def test_follow_index(self, setup_es, setup_params):

        setup_es["remote-cluster"].info.return_value = as_future(
            {
                "cluster_name": "remote_test_cluster",
                "nodes": {
                    "ZrKjLJ1cT6eXblbjwMkkFA": {
                    "transport_address": "127.0.0.1:39320",
                    },
                    "ZrKjLJ1cT6eXblbjwMkkFB": {
                    "transport_address": "127.0.0.2:39320",
                    }
                }
            }
        )

        license = {
            "license": {
                "status": "active",
                "uid": "ff0d138d-176a-4a8a-bf93-3ce1dbb4466b",
                "type": "trial",
                "issue_date": "2022-08-12T04: 32: 25.581Z",
                "issue_date_in_millis": 1660278745581,
                "expiry_date": "2022-09-11T04: 32: 25.581Z",
                "expiry_date_in_millis": 1662870745581,
                "max_nodes": 1000,
                "issued_to": "cluster-1",
                "issuer": "elasticsearch",
                "start_date_in_millis": -1
            }
        }

        setup_es["remote-cluster"].license.get.return_value = as_future(license)
        setup_es["local-cluster"].license.get.return_value = as_future(license)

        setup_es["remote-cluster"].indices.get_settings.return_value = as_future(
            {
                ".ds-logs-apache.error-default-2022.08.12-000001": {
                    "settings": {
                        "index": {
                            "number_of_replicas": "0",
                        }
                    }
                },
                ".ds-logs-nginx.error-default-2022.08.12-000001": {
                    "settings": {
                        "index": {
                            "number_of_replicas": "1",
                        }
                    }
                }
            }
        )

        setup_es["local-cluster"].cluster.put_settings.return_value = as_future({})
        setup_es["local-cluster"].cluster.remote_info.return_value = as_future(
            {
                "remote_test_cluster": {
                    "connected": False,
                    "mode": "sniff",
                    "seeds": ["127.0.0.1:39320"],
                    "num_nodes_connected": 1,
                    "max_connections_per_cluster": 3,
                    "initial_connect_timeout": "30s",
                    "skip_unavailable": False
                }
            }
        )

        setup_es["remote-cluster"].indices.flush.return_value = as_future({})
        setup_es["local-cluster"].ccr.follow.return_value = as_future({})
        setup_es["local-cluster"].cluster.health.return_value = as_future({})

        follow_index = FollowIndexRunner()
        await follow_index(setup_es, setup_params)

        setup_es["remote-cluster"].indices.flush.assert_has_calls(
            [
                mock.call(
                    index=".ds-logs-apache.error-default-2022.08.12-000001",
                    wait_if_ongoing=True,
                    request_timeout=7200,
                ),
                mock.call(
                    index=".ds-logs-nginx.error-default-2022.08.12-000001",
                    wait_if_ongoing=True,
                    request_timeout=7200,
                ),
            ]

        )

        setup_es["local-cluster"].ccr.follow.assert_has_calls(
            [
                mock.call(
                    index=".ds-logs-apache.error-default-2022.08.12-000001",
                    wait_for_active_shards="1",
                    body={
                        "leader_index": ".ds-logs-apache.error-default-2022.08.12-000001",
                        "remote_cluster": "remote_test_cluster",
                        "read_poll_timeout": "5m",
                        "settings": {
                            "index.number_of_replicas": "0"
                        },
                    },
                    request_timeout=7200
                ),
                mock.call(
                    index=".ds-logs-nginx.error-default-2022.08.12-000001",
                    wait_for_active_shards="1",
                    body={
                        "leader_index": ".ds-logs-nginx.error-default-2022.08.12-000001",
                        "remote_cluster": "remote_test_cluster",
                        "read_poll_timeout": "5m",
                        "settings": {
                            "index.number_of_replicas": "1"
                        },
                    },
                    request_timeout=7200
                ),
            ]
        )

    @pytest.mark.asyncio
    async def test_follow_index_invalid_license(self, setup_es, setup_params):



        setup_es["remote-cluster"].info.return_value = as_future(
            {
                "cluster_name": "remote_test_cluster",
                "nodes": {
                    "ZrKjLJ1cT6eXblbjwMkkFA": {
                    "transport_address": "127.0.0.1:39320",
                    },
                    "ZrKjLJ1cT6eXblbjwMkkFB": {
                    "transport_address": "127.0.0.2:39320",
                    }
                }
            }
        )

        license = {
            "license": {
                "status": "active",
                "uid": "ff0d138d-176a-4a8a-bf93-3ce1dbb4466b",
                "type": "basic",
                "issue_date": "2022-08-12T04: 32: 25.581Z",
                "issue_date_in_millis": 1660278745581,
                "expiry_date": "2022-09-11T04: 32: 25.581Z",
                "expiry_date_in_millis": 1662870745581,
                "max_nodes": 1000,
                "issued_to": "cluster-1",
                "issuer": "elasticsearch",
                "start_date_in_millis": -1
            }
        }

        setup_es["remote-cluster"].license.get.return_value = as_future(license)
        setup_es["local-cluster"].license.get.return_value = as_future(license)

        setup_es["remote-cluster"].indices.get_settings.return_value = as_future({})

        setup_es["local-cluster"].cluster.put_settings.return_value = as_future({})
        setup_es["local-cluster"].cluster.remote_info.return_value = as_future({})
        setup_es["remote-cluster"].indices.flush.return_value = as_future({})
        setup_es["local-cluster"].ccr.follow.return_value = as_future({})
        setup_es["local-cluster"].cluster.health.return_value = as_future({})

        follow_index = FollowIndexRunner()
        required_licenses = ["trial", "platinum", "enterprise"]
        with pytest.raises(BaseException) as e:
            await follow_index(setup_es, setup_params)

        assert (
            "Cannot use license type(s) [basic, basic] for CCR features. "
            f"All clusters must use one of [{required_licenses}]" in str(e)
        )


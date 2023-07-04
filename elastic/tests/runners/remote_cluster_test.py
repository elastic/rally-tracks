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
from shared.runners.remote_cluster import (
    ConfigureCrossClusterReplication,
    ConfigureRemoteClusters,
    MultiClusterWrapper,
)
from tests import as_future


class TestConfigureRemoteClusters:
    @pytest.fixture
    @mock.patch("elasticsearch.Elasticsearch")
    def setup_es(self, es):
        cluster_0 = es
        cluster_1 = copy.deepcopy(es)
        cluster_2 = copy.deepcopy(es)
        cluster_3 = copy.deepcopy(es)
        cluster_4 = copy.deepcopy(es)
        local_cluster = copy.deepcopy(es)

        multi_es = {
            "cluster_0": cluster_0,
            "cluster_1": cluster_1,
            "cluster_2": cluster_2,
            "cluster_3": cluster_3,
            "cluster_4": cluster_4,
            "local_cluster": local_cluster,
        }
        return multi_es

    @pytest.fixture
    def setup_params(self):
        params = {"local-cluster": "local_cluster"}
        return params

    def test_get_seed_nodes_multiple_nodes(self):
        nodes_resp = {
            "cluster_name": "cluster_name",
            "nodes": {
                "ZrKjLJ1cT6eXblbjwMkkFA": {
                    "transport_address": f"127.0.0.1:39320",
                    "roles": ["data_hot", "remote_cluster_client"],
                },
                "ZrKjLJ1cT6eXblbjwMkkFb": {
                    "transport_address": f"127.0.0.2:39320",
                    "roles": ["master"],
                },
            },
        }
        assert ConfigureRemoteClusters._get_seed_nodes(nodes_resp) == ["127.0.0.1:39320"]

    def test_get_seed_nodes_single_node(self):
        nodes_resp = {
            "cluster_name": "cluster_name",
            "nodes": {
                "ZrKjLJ1cT6eXblbjwMkkFA": {
                    "transport_address": "127.0.0.1:39320",
                    "roles": ["master", "data_hot", "remote_cluster_client"],
                }
            },
        }
        assert ConfigureRemoteClusters._get_seed_nodes(nodes_resp) == ["127.0.0.1:39320"]

    def test_get_seed_nodes_no_nodes(self):
        nodes_resp = {
            "cluster_name": "cluster_name",
            "nodes": {
                "ZrKjLJ1cT6eXblbjwMkkFA": {
                    "transport_address": "127.0.0.1:39320",
                    "roles": ["data_hot"],
                }
            },
        }

        with pytest.raises(BaseException) as e:
            ConfigureRemoteClusters._get_seed_nodes(nodes_resp)

        assert (
            "Unable to retrieve any seed nodes for cluster [cluster_name]. Ensure that the node(s) have the "
            "'remote_cluster_client' node role assigned under 'node.roles'." in str(e)
        )

    @pytest.mark.asyncio
    async def test_configure_remote_cluster(self, setup_es, setup_params):
        """
        The aim of this Runner is to configure a CCS architecture where a 'local' cluster can fanout searches across
        all remote clusters. The 'remote' clusters are also configured to connect back to the 'local' in preparation
        for CCR.
        """
        for i, (cluster_name, cluster_client) in enumerate(setup_es.items()):
            cluster_client.nodes.info.return_value = as_future(
                {
                    "cluster_name": cluster_name,
                    "nodes": {
                        "ZrKjLJ1cT6eXblbjwMkkFA": {
                            "transport_address": f"{i}27.0.0.1:39320",
                            "roles": ["data_hot", "remote_cluster_client"],
                        },
                        "ZrKjLJ1cT6eXblbjwMkkFB": {
                            "transport_address": f"{i}27.0.0.2:39320",
                            "roles": ["remote_cluster_client"],
                        },
                    },
                }
            )

            cluster_client.cluster.put_settings.return_value = as_future({})

            if cluster_name == "local_cluster":
                # 'local*' cluster is connected to all 'remote_*' clusters
                cluster_client.cluster.remote_info.return_value = as_future(
                    {
                        "remote_cluster_0": {
                            "connected": True,
                        },
                        "remote_cluster_1": {
                            "connected": True,
                        },
                        "remote_cluster_2": {
                            "connected": True,
                        },
                        "remote_cluster_3": {
                            "connected": True,
                        },
                        "remote_cluster_4": {
                            "connected": True,
                        },
                    }
                )
            else:
                # 'remote_*' clusters only have 1 remote to the 'local*' cluster
                cluster_client.cluster.remote_info.return_value = as_future(
                    {
                        "local_cluster": {
                            "connected": True,
                        }
                    }
                )

        cfg_remote_cluster = ConfigureRemoteClusters()
        await cfg_remote_cluster(setup_es, setup_params)

        for i, (cluster_name, cluster_client) in enumerate(setup_es.items()):
            if cluster_name == "local_cluster":
                # 'local*' cluster is connected to all 'remote_*' clusters
                cluster_client.cluster.put_settings.assert_has_calls(
                    [
                        mock.call(
                            body={
                                "persistent": {
                                    "cluster.remote.remote_cluster_0.seeds": ["027.0.0.1:39320", "027.0.0.2:39320"],
                                }
                            }
                        ),
                        mock.call(
                            body={
                                "persistent": {
                                    "cluster.remote.remote_cluster_1.seeds": ["127.0.0.1:39320", "127.0.0.2:39320"],
                                }
                            }
                        ),
                        mock.call(
                            body={
                                "persistent": {
                                    "cluster.remote.remote_cluster_2.seeds": ["227.0.0.1:39320", "227.0.0.2:39320"],
                                }
                            }
                        ),
                        mock.call(
                            body={
                                "persistent": {
                                    "cluster.remote.remote_cluster_3.seeds": ["327.0.0.1:39320", "327.0.0.2:39320"],
                                }
                            }
                        ),
                        mock.call(
                            body={
                                "persistent": {
                                    "cluster.remote.remote_cluster_4.seeds": ["427.0.0.1:39320", "427.0.0.2:39320"],
                                }
                            }
                        ),
                    ]
                )

            else:
                # all 'remote' clusters should have been configured to connect to the 'local'
                cluster_client.cluster.put_settings.assert_has_calls(
                    [
                        mock.call(
                            body={
                                "persistent": {
                                    "cluster.remote.local_cluster.seeds": ["527.0.0.1:39320", "527.0.0.2:39320"],
                                }
                            }
                        )
                    ]
                )

    @pytest.mark.asyncio
    async def test_configure_remote_cluster_not_connected(self, setup_es, setup_params):
        for i, (cluster_name, cluster_client) in enumerate(setup_es.items()):
            cluster_client.nodes.info.return_value = as_future(
                {
                    "cluster_name": cluster_name,
                    "nodes": {
                        "ZrKjLJ1cT6eXblbjwMkkFA": {
                            "transport_address": f"{i}27.0.0.1:39320",
                            "roles": ["data_hot", "remote_cluster_client"],
                        },
                        "ZrKjLJ1cT6eXblbjwMkkFB": {
                            "transport_address": f"{i}27.0.0.2:39320",
                            "roles": [],
                        },
                    },
                }
            )

            cluster_client.cluster.put_settings.return_value = as_future({})

            if cluster_name == "local_cluster":
                # 'local*' cluster is connected to all 'remote_*' clusters
                # only some are not connected, but we should still error out here
                cluster_client.cluster.remote_info.return_value = as_future(
                    {
                        "remote_cluster_0": {
                            "connected": True,
                        },
                        "remote_cluster_1": {
                            "connected": False,
                        },
                        "remote_cluster_2": {
                            "connected": True,
                        },
                        "remote_cluster_3": {
                            "connected": False,
                        },
                        "remote_cluster_4": {
                            "connected": True,
                        },
                    }
                )
            else:
                # 'remote_*' clusters only have 1 remote to the 'local*' cluster
                cluster_client.cluster.remote_info.return_value = as_future(
                    {
                        "local_cluster": {
                            "connected": True,
                        }
                    }
                )

        cfg_remote_clusters = ConfigureRemoteClusters()
        with pytest.raises(BaseException) as e:
            await cfg_remote_clusters(setup_es, setup_params)

        assert (
            "Unable to connect [local_cluster] to cluster [remote_cluster_1]. Check each cluster's "
            "logs for more information on why the connection failed." in str(e)
        )


class TestConfigureCrossClusterReplication:
    @pytest.fixture
    @mock.patch("elasticsearch.Elasticsearch")
    def setup_es(self, es):
        cluster_0 = es
        cluster_1 = copy.deepcopy(es)
        cluster_2 = copy.deepcopy(es)
        cluster_3 = copy.deepcopy(es)
        cluster_4 = copy.deepcopy(es)
        local_cluster = copy.deepcopy(es)

        multi_es = {
            "cluster_0": cluster_0,
            "cluster_1": cluster_1,
            "cluster_2": cluster_2,
            "cluster_3": cluster_3,
            "cluster_4": cluster_4,
            "source_cluster": local_cluster,
        }
        return multi_es

    @pytest.fixture
    def setup_params(self):
        params = {"source-cluster": "source_cluster", "index": "logs-*"}
        return params

    @pytest.mark.asyncio
    async def test_configure_ccr(self, setup_es, setup_params):
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
                "start_date_in_millis": -1,
            }
        }

        for cluster_name, cluster_client in setup_es.items():
            cluster_client.license.get.return_value = as_future(license)
            cluster_client.indices.flush.return_value = as_future({})

        setup_es["source_cluster"].indices.get_settings.return_value = as_future(
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
                },
            }
        )

        for cluster_name, cluster_client in setup_es.items():
            cluster_client.indices.flush.return_value = as_future({})
            if cluster_name != "source_cluster":
                cluster_client.ccr.follow.return_value = as_future({})
                cluster_client.cluster.health.return_value = as_future({})

        cfg_ccr = ConfigureCrossClusterReplication()
        await cfg_ccr(setup_es, setup_params)

        setup_es["source_cluster"].indices.flush.assert_has_calls(
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

        for cluster_name, cluster_client in setup_es.items():
            if cluster_name != "source_cluster":
                cluster_client.ccr.follow.assert_has_calls(
                    [
                        mock.call(
                            index=".ds-logs-apache.error-default-2022.08.12-000001",
                            wait_for_active_shards="1",
                            body={
                                "leader_index": ".ds-logs-apache.error-default-2022.08.12-000001",
                                "remote_cluster": "source_cluster",
                                "read_poll_timeout": "5m",
                                "settings": {"index.number_of_replicas": "0"},
                            },
                            request_timeout=7200,
                        ),
                        mock.call(
                            index=".ds-logs-nginx.error-default-2022.08.12-000001",
                            wait_for_active_shards="1",
                            body={
                                "leader_index": ".ds-logs-nginx.error-default-2022.08.12-000001",
                                "remote_cluster": "source_cluster",
                                "read_poll_timeout": "5m",
                                "settings": {"index.number_of_replicas": "1"},
                            },
                            request_timeout=7200,
                        ),
                    ]
                )

    @pytest.mark.asyncio
    async def test_configure_ccr_invalid_license(self, setup_es, setup_params):
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
                "start_date_in_millis": -1,
            }
        }
        for cluster_name, cluster_client in setup_es.items():
            cluster_client.license.get.return_value = as_future(license)
            if cluster_name != "source_cluster":
                cluster_client.ccr.follow.return_value = as_future({})
                cluster_client.cluster.health.return_value = as_future({})

        setup_es["source_cluster"].indices.get_settings.return_value = as_future({})
        setup_es["source_cluster"].indices.flush.return_value = as_future({})

        cfg_ccr = ConfigureCrossClusterReplication()
        with pytest.raises(BaseException) as e:
            await cfg_ccr(setup_es, setup_params)

        assert (
            "Cluster [source_cluster] cannot use license type [basic] for CCR features. "
            f"All clusters must use one of [{cfg_ccr.required_licenses}]" in str(e)
        )


class TestMultiClusterWrapper:
    @pytest.fixture
    @mock.patch("elasticsearch.Elasticsearch")
    def setup_es(self, es):
        cluster_0 = es
        cluster_1 = copy.deepcopy(es)
        cluster_2 = copy.deepcopy(es)
        cluster_3 = copy.deepcopy(es)
        cluster_4 = copy.deepcopy(es)
        default_cluster = copy.deepcopy(es)

        multi_es = {
            "cluster_0": cluster_0,
            "cluster_1": cluster_1,
            "cluster_2": cluster_2,
            "cluster_3": cluster_3,
            "cluster_4": cluster_4,
            "default": default_cluster,
        }
        return multi_es

    @pytest.fixture
    def setup_params(self):
        params = {
            "base-operation-type": "unit-test-single-cluster-runner",
            "ignore-clusters": ["cluster_0", "cluster_1"],
            "base-runner-param": "test",
        }
        return params

    @pytest.mark.asyncio
    @mock.patch("shared.runners.remote_cluster.runner_for")
    async def test_wraps_correctly(self, mocked_runner_for, setup_es, setup_params):
        class UnitTestSingleClusterRunner:
            async def __call__(self, es, params):
                es.test_method(params["base-runner-param"])
                return {"weight": 1, "unit": "ops", "test": "value"}

            def __str__(self):
                return "UnitTestSingleClusterRunner"

        base_runner = UnitTestSingleClusterRunner()
        mocked_runner_for.return_value = base_runner

        mcw = MultiClusterWrapper()
        r = await mcw(setup_es, setup_params)

        for cluster_name, _ in setup_es.items():
            # skipped clusters
            if cluster_name not in ["cluster_0", "cluster_1"]:
                setup_es[cluster_name].test_method.assert_has_calls([mock.call(setup_params["base-runner-param"])])

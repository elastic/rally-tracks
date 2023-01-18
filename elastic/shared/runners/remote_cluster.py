import asyncio
import copy

from elasticsearch import ElasticsearchException
from esrally.driver.runner import Runner, runner_for, unwrap

"""
Runners for configuring a typical CCS/CCR architecture, where we have a central 'local' cluster and many 'remote'
clusters.

These runners:
1. configure bi-directional connections between 'local-cluster' and all other remaining 'remote' clusters
2. configure CCR where the 'source-cluster' cluster is used as the source for all other remaining
    'remote' clusters to follow from
"""


class ConfigureRemoteClusters(Runner):
    """
    Runner to bi-directionally connect the specified local-cluster to all other clusters specified in the `target-hosts` parameter.
    * `local-cluster`: (mandatory) the name of the local cluster specified in `target-hosts` parameters.
    """

    multi_cluster = True

    def __init__(self):
        super().__init__()

    @staticmethod
    def _get_seed_nodes(nodes_api_response):
        seed_nodes = []

        # naively avoid targeting masters on multi node clusters
        for n in nodes_api_response["nodes"].values():
            if "remote_cluster_client" in n["roles"] and "master" not in n["roles"]:
                seed_nodes.append(n["transport_address"])

        # maybe we have a single node cluster, or all nodes have all roles
        if len(seed_nodes) < 1:
            for n in nodes_api_response["nodes"].values():
                if "remote_cluster_client" in n["roles"]:
                    seed_nodes.append(n["transport_address"])

        if len(seed_nodes) < 1:
            raise BaseException(
                f"Unable to retrieve any seed nodes for cluster [{nodes_api_response['cluster_name']}]. "
                "Ensure that the node(s) have the 'remote_cluster_client' node role assigned under 'node.roles'."
            )

        return seed_nodes

    async def _configure_remote_cluster(self, local_cluster_client, local_cluster_name, remote_cluster_identifier, remote_seed_nodes):
        local_settings_body = {"persistent": {f"cluster.remote.{remote_cluster_identifier}.seeds": remote_seed_nodes}}

        self.logger.info(f"put cluster settings [{repr(local_settings_body)}] to the local cluster [{local_cluster_name}]")
        await local_cluster_client.cluster.put_settings(body=local_settings_body)

        self.logger.info(f"checking that cluster [{local_cluster_name}] is connected to cluster [{remote_cluster_identifier}]")
        local_info = await local_cluster_client.cluster.remote_info()
        if not local_info.get(remote_cluster_identifier, {}).get("connected"):
            self.logger.error(f"Unable to connect [{local_cluster_name}] to cluster [{remote_cluster_identifier}]")
            raise BaseException(
                f"Unable to connect [{local_cluster_name}] to cluster [{remote_cluster_identifier}]. "
                f"Check each cluster's logs for more information on why the connection failed."
            )

    async def __call__(self, multi_es, params):

        local_cluster_name = params["local-cluster"]
        local_es = multi_es[local_cluster_name]
        self.logger.info(f"retrieving nodes from the local cluster [{local_es}]")
        local_nodes_resp = await local_es.nodes.info()
        local_seed_nodes = self._get_seed_nodes(local_nodes_resp)

        # remove our 'local-cluster' from the overall list of es clients
        remaining_es_clients = copy.copy(multi_es)
        remaining_es_clients.pop(local_cluster_name)

        for remote_cluster_name, remote_cluster_client in remaining_es_clients.items():
            # retrieve seed nodes from the remote cluster
            self.logger.info(
                f"retrieving nodes from the remote cluster [{remote_cluster_name}]",
            )
            remote_nodes_resp = await remote_cluster_client.nodes.info()
            remote_seed_nodes = self._get_seed_nodes(remote_nodes_resp)
            # ensure the identifier used as the 'remote' name matches the "remote*" pattern for use in query tasks
            remote_cluster_identifier = f"remote_{remote_cluster_name}"

            # connect 'local' cluster to 'remote' cluster
            await self._configure_remote_cluster(
                local_cluster_client=local_es,
                local_cluster_name=local_cluster_name,
                remote_cluster_identifier=remote_cluster_identifier,
                remote_seed_nodes=remote_seed_nodes,
            )

            # connect 'remote' cluster to 'local' cluster
            await self._configure_remote_cluster(
                local_cluster_client=remote_cluster_client,
                local_cluster_name=remote_cluster_name,
                remote_cluster_identifier=local_cluster_name,
                remote_seed_nodes=local_seed_nodes,
            )

    def __repr__(self, *args, **kwargs):
        return "configure-remote-clusters"


class ConfigureCrossClusterReplication(Runner):
    """
    Runner that configures all other clusters specified in `target-hosts` to follow specified indices from the 'source-cluster'.
    * `source-cluster`: (mandatory) the name of the cluster specified in `target-hosts` parameters from which to follow indices.
    * `index`: (mandatory) the pattern of indices to be replicated
    * `request-timeout`: (optional) the timeout of this runner. Defaults to 7200
    """

    multi_cluster = True

    def __init__(self):
        super().__init__()
        self.required_licenses = ["trial", "platinum", "enterprise"]

    def check_license_type(self, cluster_name, license_type):
        if license_type not in self.required_licenses:
            raise BaseException(
                f"Cluster [{cluster_name}] cannot use license type [{license_type}] "
                f"for CCR features. All clusters must use one of [{self.required_licenses}]]"
            )
        return

    async def _follow_indices(self, params, source_cluster_name, source_cluster_client, following_cluster_name, following_cluster_client):
        request_timeout = params.get("request-timeout", 7200)

        following_license = await following_cluster_client.license.get()
        source_license = await source_cluster_client.license.get()
        source_license_type = source_license.get("license", {}).get("type")
        following_license_type = following_license.get("license", {}).get("type")

        self.check_license_type(source_cluster_name, source_license_type)
        self.check_license_type(following_cluster_name, following_license_type)

        # fetch the indices from the source cluster
        source_indices = await source_cluster_client.indices.get_settings(index=params["index"], request_timeout=request_timeout)

        self.logger.info(
            f"connected to source cluster [{source_cluster_name}] from [{following_cluster_name}]; indices [{repr(list(source_indices))}]"
        )
        for index, settings in source_indices.items():
            # flush on the source index to speed up the replication as only file-based recovery will occur.
            self.logger.info(f"flushing source index [{index}] on [{source_cluster_name}]")
            await source_cluster_client.indices.flush(index=index, wait_if_ongoing=True, request_timeout=request_timeout)
            self.logger.info(f"starting to follow index [{index}] from [{source_cluster_name}] on [{following_cluster_name}]")
            number_of_replicas = settings["settings"]["index"]["number_of_replicas"]
            follow_body = {
                "leader_index": index,
                "remote_cluster": source_cluster_name,
                "read_poll_timeout": "5m",  # large value to reduce the traffic between clusters
                "settings": {"index.number_of_replicas": number_of_replicas},
            }

            try:
                await following_cluster_client.ccr.follow(
                    index=index, wait_for_active_shards="1", body=follow_body, request_timeout=request_timeout
                )
            except ElasticsearchException as e:
                msg = f"Failed to follow index [{index}] from [{source_cluster_name}] on [{following_cluster_name}]; [{e}]"
                raise BaseException(msg)

            self.logger.info(f"index [{index}] was replicated from [{source_cluster_name}] to [{following_cluster_name}]")

            await following_cluster_client.cluster.health(
                index=index,
                wait_for_no_initializing_shards=True,
                wait_for_status="green",
                timeout=f"{request_timeout}s",
                request_timeout=request_timeout,
            )

    async def __call__(self, multi_es, params):
        # this is the cluster we want to follow/replicate from
        source_cluster_client = multi_es[params["source-cluster"]]
        source_cluster_name = params["source-cluster"]

        remaining_es_clients = copy.copy(multi_es)
        remaining_es_clients.pop(params["source-cluster"])

        coroutines = []
        # configure CCR on all 'remote' clusters to follow indices in the 'source-cluster'
        for following_cluster_name, following_cluster_client in remaining_es_clients.items():
            coroutines.append(
                self._follow_indices(params, source_cluster_name, source_cluster_client, following_cluster_name, following_cluster_client)
            )

        await asyncio.gather(*coroutines)

    def __repr__(self, *args, **kwargs):
        return "configure-ccr"


class MultiClusterWrapper(Runner):
    """
    Wraps the provided runner (`base-operation-type`) to execute across all clusters provided in Rally's CLI arg `target-hosts`.
    * `base-operation-type`: (mandatory) the name of the runner for which to 'wrap'
    * `ignore-clusters`: (optional) A list of cluster name(s) as provided in `target-hosts` to skip over and not execute on
    the runner
    """

    multi_cluster = True

    def __init__(self):
        super().__init__()

    async def __call__(self, multi_es, params):
        base_runner = params.get("base-operation-type")
        coroutines = []
        for cluster_name, cluster_client in multi_es.items():
            if cluster_name in params.get("ignore-clusters", []):
                self.logger.info(f"Multi cluster wrapped runner [{base_runner}] ignoring cluster [{cluster_name}].")
                continue
            runner_for_op = unwrap(runner_for(base_runner))
            self.logger.info(f"Multi cluster wrapped runner [{base_runner}] executing on cluster [{cluster_name}].")
            # just call base runner op, don't mess with 'return' values
            coroutines.append(runner_for_op(cluster_client, params))
        await asyncio.gather(*coroutines)

    def __repr__(self, *args, **kwargs):
        return "multi-cluster-wrapper"

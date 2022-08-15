import time
import math

from esrally.driver.runner import Runner
from elasticsearch import ElasticsearchException

"""
Runners for benchmarking multi-clusters. Once these runners are stable, we can move them to Rally.
"""


class ConfigureRemoteCluster(Runner):
    """
    Runner to configure the remote cluster connection on the local cluster to the remote cluster.
    * `local-cluster`: (mandatory) the name of the local cluster specified in `target-hosts` parameters.
    * `remote-cluster`: (mandatory) the name of the remote cluster specified in `target-hosts` parameters
    * `remote-connection-name`: (optional) the name of the remote connection;
    *                           defaults to the name of the remote cluster
    """
    multi_cluster = True

    def __init__(self):
        super().__init__()

    async def __call__(self, multi_es, params):
        # retrieve seed nodes from the remote cluster
        remote_es = multi_es[params["remote-cluster"]]
        self.logger.info(f"retrieving nodes from the remote cluster [{params['remote-cluster']}]", )
        remote_nodes_resp = await remote_es.nodes.info()
        remote_seed_nodes = [n["transport_address"] for n in remote_nodes_resp["nodes"].values()]
        remote_cluster = params.get("remote-connection-name", remote_nodes_resp["cluster_name"])

        # put the cluster setting to the local cluster
        settings_body = {
            "persistent": {
                f"cluster.remote.{remote_cluster}.seeds": remote_seed_nodes
            }
        }
        self.logger.info(f"put cluster settings [{repr(settings_body)}] to the local cluster [{params['local-cluster']}]")
        local_es = multi_es[params["local-cluster"]]
        await local_es.cluster.put_settings(body=settings_body)

        self.logger.info(f"checking that cluster [{params['local-cluster']}] is connected to cluster [{params['remote-cluster']}]")
        local_info = await local_es.cluster.remote_info()
        if not local_info.get(remote_cluster, {}).get("connected"):
            self.logger.error(f"Unable to connect [{params['local-cluster']}] to cluster [{params['remote-cluster']}]")
            raise BaseException(
                f"Unable to connect [{params['local-cluster']}] to cluster [{remote_cluster}]. "
                f"Check each cluster's logs for more information on why the connection failed."
            )

    def __repr__(self, *args, **kwargs):
        return "configure-remote-cluster"


class FollowIndexRunner(Runner):
    """
    Runner to replicate and follow indices from the remote cluster to the local cluster using CCR.
    * `local-cluster`: (mandatory) the name of the local cluster specified in `target-hosts` parameters.
    * `remote-cluster`: (mandatory) the name of the remote cluster specified in `target-hosts` parameters
    * `index`: (mandatory) the pattern of indices to be replicated
    * `request-timeout`: (optional) the timeout of this runner. Defaults to 7200
    * `remote-connection-name`: (optional) the name of the remote connection;
    *                           defaults to the name of the remote cluster
    """
    multi_cluster = True

    def __init__(self):
        super().__init__()

    async def __call__(self, multi_es, params):
        end_request_timeout = time.process_time() + params.get("request-timeout", 7200)
        required_licenses = ["trial", "platinum", "enterprise"]
        def request_timeout():
            return math.ceil(end_request_timeout - time.process_time())

        remote_es = multi_es[params["remote-cluster"]]
        local_es = multi_es[params["local-cluster"]]

        if "remote-connection-name" in params:
            remote_cluster = params["remote-connection-name"]
        else:
            remote_info_resp = await remote_es.info()
            remote_cluster = remote_info_resp["cluster_name"]

        remote_license = await remote_es.license.get()
        local_license = await local_es.license.get()
        local_license_type = local_license.get("license", {}).get("type")
        remote_license_type = remote_license.get("license", {}).get("type")

        if local_license_type not in required_licenses or remote_license_type not in required_licenses:
            raise BaseException(
                f"Cannot use license type(s) [{local_license_type}, {remote_license_type}] "
                f"for CCR features. All clusters must use one of [{required_licenses}]]"
            )

        # fetch the indices from the remote cluster
        remote_indices = await remote_es.indices.get_settings(index=params["index"],
                                                              request_timeout=request_timeout())

        self.logger.info(f"remote cluster [{remote_cluster}]; indices [{repr(list(remote_indices))}]")
        for index, settings in remote_indices.items():
            # flush on the remote index to speed up the replication as only file-based recovery will occur.
            self.logger.info(f"flushing remote index [{index}] on [{remote_cluster}]")
            await remote_es.indices.flush(index=index,
                                          wait_if_ongoing=True,
                                          request_timeout=request_timeout())
            self.logger.info(f"start following index [{index}] from [{remote_cluster}]")
            number_of_replicas = settings["settings"]["index"]["number_of_replicas"]
            follow_body = {
                "leader_index": index,
                "remote_cluster": remote_cluster,
                "read_poll_timeout": "5m",  # large value to reduce the traffic between clusters
                "settings": {
                    "index.number_of_replicas": number_of_replicas
                }
            }

            try:
                await local_es.ccr.follow(index=index,
                                      wait_for_active_shards="1",
                                      body=follow_body,
                                      request_timeout=request_timeout())
            except ElasticsearchException as e:
                msg = f"Failed to follow index [{index}]; [{e}]"
                raise BaseException(msg)

            self.logger.info(f"index [{index}] was replicated from [{remote_cluster}]")

            await local_es.cluster.health(index=index,
                                          wait_for_no_initializing_shards=True,
                                          wait_for_status="green",
                                          timeout=f"{request_timeout()}s",
                                          request_timeout=request_timeout())

    def __repr__(self, *args, **kwargs):
        return "follow-index"

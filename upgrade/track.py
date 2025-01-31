

import logging

logger = logging.getLogger(__name__)


async def restoreSnapshotIntoDatastream(es, params):
    repository_name = params["repository"]
    snapshot_name = params["snapshot"]
    # data_stream = params["data-stream"]
    num_indices = params["num-indices"]

    # index_pattern = params.get("index_pattern", "*")
    # rename_pattern = params.get("rename_pattern", "(.*)")
    # rename_replacement = params.get("rename_replacement", "\\1")
    # ignore_index_settings = params.get("ignore_index_settings")
    # storage = params.get("storage")
    # query_params = params.get("query_params", {})

    for idx in range(1, num_indices + 1):
        replacement = f'$1-{idx}'
        await es.snapshot.restore(
            repository=repository_name,
            snapshot=snapshot_name,
            wait_for_completion=True,
            body={
                "indices": "some-index",
                "ignore_unavailable": False,
                "include_global_state": False,
                "include_aliases": False,
                "rename_pattern": "(.+)",
                "rename_replacement": replacement
            })




def register(registry):
    registry.register_runner("restore-into-data-stream", restoreSnapshotIntoDatastream, async_runner=True)

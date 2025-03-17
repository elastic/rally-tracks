import asyncio
import copy

from esrally.driver.runner import Runner, runner_for, unwrap
from shared.utils.track import mandatory

"""
Runners for reindexing data streams and waiting on running reindex operations.
"""


class StartReindexDataStream(Runner):
    async def __call__(self, es, params):
        data_stream = mandatory(params, "data-stream", self)
        body = {"source": {"index": data_stream}, "mode": "upgrade"}
        await es.perform_request(method="POST", path=f"/_migration/reindex", body=body)

    def __repr__(self, *args, **kwargs):
        return "reindex-data-stream"


class WaitForReindexDataStream(Runner):
    def __init__(self):
        super().__init__()
        self._percent_completed = 0.0

    @property
    def percent_completed(self):
        return self._percent_completed

    async def __call__(self, es, params):
        data_stream = mandatory(params, "data-stream", self)
        wait_period = params.get("completion-recheck-wait-period", 1)

        done = False
        while not done:
            response = await es.perform_request(method="GET", path=f"/_migration/reindex/{data_stream}/_status")
            done = response.get("complete", False)
            if not done:
                await asyncio.sleep(wait_period)

            total_requiring_upgrade = response.get("total_indices_requiring_upgrade")
            successes = response.get("successes")
            self._percent_completed = successes / total_requiring_upgrade

    def __repr__(self, *args, **kwargs):
        return "wait-for-reindex-data-stream"


class RestoreIntoDataStream(Runner):
    def __init__(self):
        super().__init__()
        self._percent_completed = 0.0

    @property
    def percent_completed(self):
        return self._percent_completed

    async def __call__(self, es, params):
        repo = mandatory(params, "repository", self)
        snapshot = mandatory(params, "snapshot", self)
        data_stream = mandatory(params, "data-stream", self)
        num_repeats = mandatory(params, "num-times-to-repeat", self)

        # first restore without any rename
        await self.restore(es, repo, snapshot, data_stream, "(.+)", '$1')
        self._percent_completed += (1 / num_repeats)

        # since initial already has one copy, only replace n-1 times
        for num in range(num_repeats-1):
            copied_data_stream_name = data_stream + f"-copy-{num}"
            res = await self.restore(es, repo, snapshot, data_stream, "(.+)", f'$1-copy-{num}')
            print(res)
            for index in res["snapshot"]["indices"]:
                #for index in res.get("indices"):
                body = {
                    "actions": [
                        {
                            "remove_backing_index": {
                                "data_stream": copied_data_stream_name,
                                "index": index
                            }
                        },
                        {
                            "add_backing_index": {
                                "data_stream": data_stream,
                                "index": index
                            }
                        }
                    ]
                }
                await es.perform_request(method="POST", path=f"/_data_stream/modify", body=body)
            self._percent_completed += (1 / num_repeats)

    def restore(self, es, repo, snapshot, data_stream, rename_pattern, rename_replacement):
        return es.snapshot.restore(
            repository=repo,
            snapshot=snapshot,
            wait_for_completion=True,
            body={
                "indices": data_stream,
                "ignore_unavailable": False,
                "include_global_state": False,
                "include_aliases": False,
                "rename_pattern": rename_pattern,
                "rename_replacement": rename_replacement
            }
        )

    def __repr__(self, *args, **kwargs):
        return "restore-into-data-stream"

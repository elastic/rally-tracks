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

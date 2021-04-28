from copy import copy
import re

from esrally import exceptions
from esrally.track import loader

def reindex(es, params):
    result = es.reindex(body=params.get("body"), request_timeout=params.get("request_timeout"))
    return result["total"], "docs"


async def reindex_async(es, params):
    result = await es.reindex(body=params.get("body"), request_timeout=params.get("request_timeout"))
    return result["total"], "docs"

class RuntimeFieldResolver(loader.TrackProcessor):
    PATTERN = re.compile('.+-from-(.+)-using-(.+)')

    def on_after_load_track(self, t):
        for challenge in t.challenges:
            for task in challenge.schedule:
                m = self.PATTERN.match(task.name)
                if m is not None:
                    source = m[1]
                    impl = m[2].replace('-', '_')
                    task.operation = copy(task.operation)
                    task.operation.params = self._replace_field(f"{impl}.from_{source}.", task.operation.params)

    def on_prepare_track(self, track, data_root_dir):
        return True

    def _replace_field(self, field, t):
        if t == 'path' or t == 'status':
            return field + t
        if isinstance(t, list):
            return [self._replace_field(field, v) for v in t]
        if isinstance(t, dict):
            return {
                self._replace_field(field, k): self._replace_field(field, v)
                for k, v in t.items()
            }
        return t

def register(registry):
    async_runner = registry.meta_data.get("async_runner", False)
    if async_runner:
        registry.register_runner("reindex", reindex_async, async_runner=True)
    else:
        registry.register_runner("reindex", reindex)
    registry.register_track_processor(RuntimeFieldResolver())

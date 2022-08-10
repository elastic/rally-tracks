import copy
import logging


class InitialIndicesParamSource:
    def __init__(self, track, params, **kwargs):
        self.logger = logging.getLogger(__name__)
        self._orig_args = [track, params, kwargs]
        # allows to be specified for testing only
        self.track = track
        self._complete = False
        self.infinite = False
        self._params = params
        self.kwargs = kwargs
        self._track_id = track.selected_challenge_or_default.parameters["track-id"]
        self.logger.info(f"Using track id {self._track_id}")
        self.indices_per_client = 1
        self._client_count = 1
        self._client_index = 1
        self.current_index = 0

    def partition(self, partition_index, total_partitions):
        self.logger.info("[%s]/[%s]", partition_index, total_partitions)
        new_params = copy.deepcopy(self._params)
        new_params["client_index"] = partition_index
        new_params["client_count"] = total_partitions
        return InitialIndicesParamSource(
            self._orig_args[0], new_params, **self._orig_args[2]
        )

    def params(self):
        if self.current_index == 0:
            self._client_count = self._params["client_count"]
            self._client_index = self._params["client_index"]
            if self._client_count <= 0:
                self._complete = True
                raise StopIteration
            self.indices_per_client = (
                self._params["initial_indices_count"] / self._client_count
            )
        self.current_index += 1
        if self.current_index > self.indices_per_client:
            self._complete = True
            raise StopIteration
        lines = []
        client_index = self._client_index
        for i in range(100):
            lines.append(
                '{"create":{"_index":"%s-%d-%d"}}\n'
                % (self._params["name"], client_index, self.current_index)
            )
            lines.append('{"@timestamp":"2%03d-01-01T12:10:30Z"}\n' % i)
        return {
            "body": "".join(lines),
            "bulk-size": 100,
            "unit": "docs",
            "action-metadata-present": True,
            "param-source-stats": {
                "client": client_index
            }
        }

    @property
    def percent_completed(self):
        if not self._complete:
            return self.current_index / self.indices_per_client
        return 1.0

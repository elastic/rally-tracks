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
import glob
import json
import logging
import os
import random
import re
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from math import ceil

from esrally import exceptions
from shared.parameter_sources import DEFAULT_MAX_DATE
from shared.query_handlers import get_query_handler, is_query_handler
from shared.utils.time import (
    DateTimeValues,
    parse_date_time,
    parse_interval,
    random_duration_for_max,
)
from shared.utils.track import mandatory


class WorkflowSelectorParamSource:

    _file_sort_numeric_pattern = re.compile("([0-9]+)")

    def __init__(self, track, params, **kwargs):
        self.logger = logging.getLogger(__name__)
        self._orig_args = [track, params, kwargs]
        self._params = params
        self.infinite = True
        self.workflows = []
        self.workflow_handlers = {}
        workflow_folder = os.path.join(track.root, params.get("workflows-folder", "workflows"))
        self.workflow = mandatory(params, "workflow", "composite")
        # prefer the seed passed by partition if more than 1 client
        self.task_offset = mandatory(params, "task-offset", "composite")
        self.random_seed = params.get(
            "random-seed",
            track.selected_challenge_or_default.parameters.get("random-seed"),
        )
        # seed here is to ensure repeatable durations
        random.seed(self.random_seed)
        self.logger.info("Workflow [%s] is using seed [%s]", self.workflow, self.random_seed)
        self.number_of_tasks = track.selected_challenge_or_default.parameters.get("number-of-workflows")
        # for testing purposes only we allow a configurable now function
        self._utc_now = kwargs.get("utc_now", datetime.utcnow)
        self._init_date = self._utc_now().replace(tzinfo=timezone.utc)
        self._detailed_results = params.get(
            "detailed-results", track.selected_challenge_or_default.parameters.get("detailed-results", False)
        )
        self._workflow_target = params.get(
            "workflow-target",
            track.selected_challenge_or_default.parameters.get("workflow-target"),
        )
        self._max_time_interval = timedelta.min
        # sorted to ensure natural sort order that respects numerics
        for action_filename in sorted(
            glob.glob(os.path.join(workflow_folder, self.workflow, "*.json"), recursive=True),
            key=self.natural_sort_key,
        ):
            self.logger.debug("Loading action from file [%s]", action_filename)
            with open(action_filename, "r") as action_file:
                action = json.load(action_file)
                if "id" not in action:
                    raise exceptions.TrackConfigError(f'Action [{action_filename}] for [{self.workflow}] is missing an "id" key')
                if "requests" not in action:
                    raise exceptions.TrackConfigError(f'Action [{action_filename}] for [{self.workflow}] is missing a "requests" key')
                action_id = action["id"]
                if action_id in self.workflow_handlers:
                    raise exceptions.TrackConfigError(
                        f"Action id [{action_id}] for [{self.workflow}] is duplicated. This must be " f"unique"
                    )
                self.logger.debug(
                    "Adding action with id [%s] to workflow [%s]",
                    action_id,
                    self.workflow,
                )
                self.workflows.append((action_id, action))
                if self._detailed_results:
                    # enable detailed results on every query
                    self.set_detailed_results(action)
                if self._workflow_target:
                    # override captured query targets with enabled integrations
                    self.set_target_index(action)
                request_params = params.get("request-params", {})
                WorkflowSelectorParamSource.stringify_bool(request_params)
                if request_params:
                    self.set_request_params(action, request_params)
                query_handlers = self.get_query_handlers(action, queries=[])
                time_interval = WorkflowSelectorParamSource.get_max_time_interval(query_handlers)
                if time_interval and time_interval > self._max_time_interval:
                    self._max_time_interval = time_interval
                self.workflow_handlers[action_id] = query_handlers

        if len(self.workflows) == 0:
            raise exceptions.TrackConfigError(f"No actions loaded. " f"[{workflow_folder}] contains no " f"action files")
        self.current_index = 0
        self._min_date = parse_date_time(
            params.get(
                "query-min-date",
                track.selected_challenge_or_default.parameters.get("query-min-date"),
            )
        )

        self._max_date = parse_date_time(
            params.get(
                "query-max-date",
                track.selected_challenge_or_default.parameters.get("query-max-date"),
            )
        )
        self._max_date_start = parse_date_time(
            params.get(
                "query-max-date-start",
                track.selected_challenge_or_default.parameters.get("query-max-date-start"),
            )
        )
        if self._max_date and self._max_date_start:
            raise exceptions.TrackConfigError(
                f"Error in {self.workflow} configuration. " "Only one of 'query-max-date' and 'query-max-date-start' can be defined."
            )
        elif self._max_date is None and self._max_date_start is None:
            # must set default here, or else conflict check with query-max-date-start is not possible
            self._max_date = parse_date_time(DEFAULT_MAX_DATE)
        self._avg_query_duration = parse_interval(
            params.get(
                "query-average-interval",
                track.selected_challenge_or_default.parameters.get("query-average-interval"),
            )
        )
        # int, in seconds. for testing purposes
        self._min_query_duration = kwargs.get("min_query_duration", 15 * 60)

        # using the max time interval we generate an upper bound for the duration - all other generated durations will
        # be scaled using this. It can be greater than (self._max_date - self._min_date) or less than the min.
        self.max_possible_duration = (datetime.max - datetime.min).total_seconds()
        if self._min_date and self._max_date:
            self.max_possible_duration = int((self._max_date - self._min_date).total_seconds())
        self.max_query_duration = random_duration_for_max(
            self._avg_query_duration,
            self._min_query_duration,
            self.max_possible_duration,
        )

    @staticmethod
    def stringify_bool(request_params):
        for key, value in request_params.items():
            if isinstance(value, bool):
                request_params[key] = "true" if value else "false"

    def set_target_index(self, action):
        if isinstance(action, dict):
            if "operation-type" in action and action["operation-type"] == "search":
                action["index"] = self._workflow_target
            else:
                for key, value in action.items():
                    self.set_target_index(value)
        elif isinstance(action, list):
            for value in action:
                self.set_target_index(value)

    def set_detailed_results(self, action):
        if isinstance(action, dict):
            if "operation-type" in action and action["operation-type"] == "search":
                action["detailed-results"] = True
            else:
                for key, value in action.items():
                    self.set_detailed_results(value)
        elif isinstance(action, list):
            for value in action:
                self.set_detailed_results(value)

    def set_request_params(self, action, request_params):
        if isinstance(action, dict):
            if "operation-type" in action:
                if "request-params" in action and action["request-params"]:
                    action["request-params"] = {
                        **action["request-params"],
                        **request_params,
                    }
                else:
                    action["request-params"] = request_params
            else:
                for _, value in action.items():
                    self.set_request_params(value, request_params)
        elif isinstance(action, list):
            for value in action:
                self.set_request_params(value, request_params)

    @staticmethod
    def get_max_time_interval(query_handlers):
        max_time_interval = datetime.min - datetime.max
        for query_handler in query_handlers:
            interval = query_handler.get_time_interval()
            if interval and interval > max_time_interval:
                max_time_interval = interval
        return max_time_interval

    def get_query_handlers(self, action, queries=[]):
        if isinstance(action, dict):
            for key, value in action.items():
                # extend here if we want to support more query types in the future
                if is_query_handler(key):
                    queries.append(get_query_handler(key, value))
                else:
                    self.get_query_handlers(value, queries=queries)
        elif isinstance(action, list):
            for value in action:
                self.get_query_handlers(value, queries=queries)
        return queries

    # provides a natural sort order for filenames
    def natural_sort_key(self, filename):
        return [int(text) if text.isdigit() else text.lower() for text in self._file_sort_numeric_pattern.split(filename)]

    def partition(self, partition_index, total_partitions):
        new_params = deepcopy(self._params)
        # 10000 * ((num_workflows * partition_index) + task_id + random_seed) gives us a unique value. We offset
        # partition_index and task_id by 1 to account for 0 values
        new_params["random-seed"] = 10000 * ((self.number_of_tasks * (partition_index + 1)) + (self.task_offset + 1) + self.random_seed)
        self.logger.info(
            "Workflow [%s] client [%s]/[%s] is being partitioned and seeded with [%s]",
            self.task_offset,
            partition_index,
            total_partitions,
            new_params["random-seed"],
        )
        new_params["client_count"] = total_partitions
        new_params["client_index"] = partition_index
        return WorkflowSelectorParamSource(self._orig_args[0], new_params, **self._orig_args[2])

    def copy_and_modify_action(self, action):
        action_id = action["id"]
        if self._max_date:
            query_max_date = self._max_date
        else:
            # process fields - use the start_date + the time passed since we started, as the time
            # all dates for the action should be the same
            query_max_date = self._max_date_start + (self._utc_now().replace(tzinfo=timezone.utc) - self._init_date)

        for query_handler in self.workflow_handlers[action_id]:
            # scale the duration based on the max if set
            duration = None
            query_handler_interval = query_handler.get_time_interval()
            if query_handler_interval and self.max_query_duration:
                duration = ceil(
                    self.max_query_duration * (query_handler_interval.total_seconds() / self._max_time_interval.total_seconds())
                )
                if duration < self._min_query_duration:
                    duration = self._min_query_duration
                duration = timedelta(seconds=duration)
                self.logger.info(
                    "Using duration of [%s]s for workflow [%s] and action [%s]",
                    duration.total_seconds(),
                    self.workflow,
                    action_id,
                )

            date_data = DateTimeValues(min_date=self._min_date, max_date=query_max_date, duration=duration)
            # this modifies these changes by ref - not thread safe
            query_handler.process(date_data)
        # always clone the dictionary as we dont' have guarantees of order in rally - deepcopy
        return deepcopy(action)

    # currently we sequentially consume the workflow's actions until its complete
    def params(self):
        self.logger.info(
            "Using action with index [%s] for workflow [%s]",
            self.current_index,
            self.workflow,
        )
        action = self.copy_and_modify_action(self.workflows[self.current_index][1])
        self.current_index = (self.current_index + 1) % len(self.workflows)
        if self.current_index == 0:
            self.max_query_duration = random_duration_for_max(
                self._avg_query_duration,
                self._min_query_duration,
                self.max_possible_duration,
            )
        self.logger.debug("Action [%s]", action)
        # pending https://github.com/elastic/rally/issues/1156 it would be nice to return statistics for the query
        # here e.g. the time range
        return action

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

import logging
import random

from shared.utils.track import mandatory


class WorkflowScheduler:
    """
    This scheduler is for use with the WorkflowSelectorParamSource source only.
    It allows the execution timing of a workflow to model a real user interaction. Each workflow consists of a series
    of actions - currently each action is a composite request and represents a user performing a UI function e.g.
    loading a dashboard. The actions are yielded by the WorkflowSelectorParamSource and executed sequentially.
    The timing between actions is controlled by an exponential distribution to result in execution times being Poisson
    distributed. This is controlled by the parameter 'think-time-interval'.
    When all actions in a workflow are exhausted, we consider its execution to be complete from a user perspective.
    The action index is reset to 0 and the workflow scheduled for execution using a different exponential rate
    determined by the parameter 'workflow-interval'. This also results in workflows executions being poisson
    distributed. This scheduler detects whether the execution should be delayed by a think-time-interval or
    workflow-interval by introspecting the parameter source for the current action index i.e. if current_index==0 use
    the workflow-interval else use think-time-interval.

    The random generation of intervals is seeded, to ensure deterministic values across different executions - allowing
    query loads to be repeated and compared.
    """

    def __init__(self, task):
        self.logger = logging.getLogger(__name__)
        self.workflow_rate = 1 / mandatory(
            task.params, "workflow-interval", "composite"
        )
        self.think_rate = 1 / mandatory(task.params, "think-time-interval", "composite")
        self.logger.info(
            f"workflow-scheduler will use workflow rate of [{self.workflow_rate}]/s"
        )
        self.logger.info(
            f"workflow-scheduler will use think rate of [{self.think_rate}]/s"
        )
        self.parameter_source = None
        self._random_generator = None
        self.first = True

    def before_request(self, now):
        pass

    def after_request(self, now, weight, unit, request_meta_data):
        pass

    def next(self, current):
        if self.first:
            self.logger.info(
                "Seeding query scheduler with [%s] for workflow [%s]",
                self.parameter_source.random_seed,
                self.parameter_source.task_offset,
            )
            self._random_generator = random.Random(self.parameter_source.random_seed)
            self.first = False
            # we offset the initial task execution
            current = current + (
                (
                    self.parameter_source.task_offset
                    / self.parameter_source.number_of_tasks
                )
                * self.workflow_rate
            )
        if self.parameter_source.current_index == 0:
            delay = self._random_generator.expovariate(self.workflow_rate)
            self.logger.info(
                "Workflow [%s] will use interval [%s] and scheduled for [%s]",
                self.parameter_source.task_offset,
                delay,
                current + delay,
            )
            return current + delay
        delay = self._random_generator.expovariate(self.think_rate)
        self.logger.info(
            "Actions for workflow [%s] will use think time of [%s] - next action scheduled for [%s]",
            self.parameter_source.task_offset,
            delay,
            current + delay,
        )
        return current + delay

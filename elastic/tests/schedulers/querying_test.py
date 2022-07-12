import random
import unittest
from unittest import TestCase

from esrally import track

from shared.parameter_sources.workflow_selector import WorkflowSelectorParamSource
from shared.schedulers.query import WorkflowScheduler
from tests.parameter_sources import StaticTrack

assertions = unittest.TestCase("__init__")


class SchedulerTestCase(TestCase):
    ITERATIONS = 10000

    # Taken from rally scheduler tests
    def assertThroughputEquals(
        self, scheduler, expected_average_throughput, msg="", relative_delta=0.05
    ):
        expected_average_rate = 1 / expected_average_throughput
        sum = 0
        for _ in range(0, self.ITERATIONS):
            tn = scheduler.next(0)
            # schedule must not go backwards in time
            self.assertGreaterEqual(tn, 0, msg)
            sum += tn
        actual_average_rate = sum / self.ITERATIONS

        expected_lower_bound = (1.0 - relative_delta) * expected_average_rate
        expected_upper_bound = (1.0 + relative_delta) * expected_average_rate

        self.assertGreaterEqual(
            actual_average_rate,
            expected_lower_bound,
            f"{msg}: expected target rate to be >= [{expected_lower_bound}] "
            f"but was [{actual_average_rate}].",
        )
        self.assertLessEqual(
            actual_average_rate,
            expected_upper_bound,
            f"{msg}: expected target rate to be <= [{expected_upper_bound}] "
            f"but was [{actual_average_rate}].",
        )


class MockParameterSource:
    def __init__(self, index, random_seed, number_of_tasks=2, task_offset=0):
        self.current_index = index
        self.random_seed = random_seed
        self.number_of_tasks = number_of_tasks
        self.task_offset = task_offset

    def set_index(self, index):
        self.current_index = index

    def set_seed(self, random_seed):
        self._random_seed = random_seed


class PoissonSchedulerTests(SchedulerTestCase):
    def test_schedule_matches_expected_throughput(self):
        parameter_source = MockParameterSource(0, 13)
        workflow_interval = random.randint(10, 1000)
        target_interval = random.randint(10, 1000)
        workflow_scheduler = WorkflowScheduler(
            track.Task(
                name="test-task",
                operation=track.Operation(
                    name="query-logging",
                    operation_type=track.OperationType.Composite.name,
                    params={"requests": []},
                ),
                params={
                    "workflow-interval": 1 / workflow_interval,
                    "think-time-interval": 1 / target_interval,
                },
            )
        )
        workflow_scheduler.parameter_source = parameter_source
        self.assertThroughputEquals(
            workflow_scheduler,
            workflow_interval,
            f"target throughput=[{workflow_interval}] " f"ops/s",
        )
        parameter_source.set_index(random.randint(1, 1000))
        self.assertThroughputEquals(
            workflow_scheduler,
            target_interval,
            f"target throughput=[{target_interval}] ops/s",
        )

    def test_schedule_is_deterministic(self):
        parameter_source = MockParameterSource(0, 13)
        workflow_interval = 30
        target_interval = 5
        workflow_scheduler = WorkflowScheduler(
            track.Task(
                name="test-task",
                operation=track.Operation(
                    name="query-logging",
                    operation_type=track.OperationType.Composite.name,
                    params={"requests": []},
                ),
                params={
                    "workflow-interval": 1 / workflow_interval,
                    "think-time-interval": 1 / target_interval,
                },
            )
        )
        workflow_scheduler.parameter_source = parameter_source
        sum = 0
        for _ in range(0, self.ITERATIONS):
            sum += workflow_scheduler.next(0)
        assertions.assertAlmostEqual(sum, 333.1079063)

    def test_schedule_offset(self):
        number_of_tasks = 5
        parameter_source = MockParameterSource(0, 13, number_of_tasks=number_of_tasks)
        workflow_interval = 30
        target_interval = 5
        for i in range(1, number_of_tasks):
            parameter_source.task_offset = i
            workflow_scheduler = WorkflowScheduler(
                track.Task(
                    name="test-task",
                    operation=track.Operation(
                        name="query-logging",
                        operation_type=track.OperationType.Composite.name,
                        params={"requests": []},
                    ),
                    params={
                        "workflow-interval": 1 / workflow_interval,
                        "think-time-interval": 1 / target_interval,
                    },
                )
            )
            workflow_scheduler.parameter_source = parameter_source
            for _ in range(0, self.ITERATIONS):
                # check it many times to make sure its consistently large
                assert workflow_scheduler.next(0) > workflow_interval * (
                    i / number_of_tasks
                )
                workflow_scheduler.first = True

    # tests that schedulers produce different schedules
    def test_schedulers_uniqueness(self):
        param_source = WorkflowSelectorParamSource(
            track=StaticTrack(
                parameters={
                    "detailed-results": True,
                    "random-seed": 13,
                    "number-of-workflows": 10,
                }
            ),
            params={
                "workflow": "a",
                "workflows-folder": "tests/parameter_sources/resources/workflows",
                "task-offset": 0,
            },
        )
        # use the same param source for both schedulers
        first_workflow_scheduler = WorkflowScheduler(
            track.Task(
                name="test-task",
                operation=track.Operation(
                    name="query-logging",
                    operation_type=track.OperationType.Composite.name,
                    params={"requests": []},
                ),
                params={"workflow-interval": 0.1, "think-time-interval": 0.2},
            )
        )
        first_workflow_scheduler.parameter_source = param_source.partition(0, 2)
        second_workflow_scheduler = WorkflowScheduler(
            track.Task(
                name="test-task",
                operation=track.Operation(
                    name="query-logging",
                    operation_type=track.OperationType.Composite.name,
                    params={"requests": []},
                ),
                params={"workflow-interval": 0.1, "think-time-interval": 0.2},
            )
        )
        second_workflow_scheduler.parameter_source = param_source.partition(1, 2)
        assert first_workflow_scheduler.next(0) != second_workflow_scheduler.next(0)

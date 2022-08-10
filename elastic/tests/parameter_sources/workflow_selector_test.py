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
import datetime
import random
import re
from math import ceil

import pytest
from esrally.exceptions import TrackConfigError, DataError

from shared.parameter_sources import DEFAULT_MAX_DATE
from shared.parameter_sources.workflow_selector import WorkflowSelectorParamSource
from shared.utils.time import parse_date_optional_time
from tests.parameter_sources import StaticTrack


class ReproducibleClock:
    def __init__(self, start):
        self.now = start

    def __call__(self, *args, **kwargs):
        return self.now

    def increment(self, seconds):
        self.now = self.now + datetime.timedelta(seconds=seconds)


class FailedWorkflowLoad(Exception):
    pass


# This tests that our real workflows can be added
@pytest.mark.asyncio
async def test_workflow_load():
    workflows = [
        "apache",
        "discover/search",
        "discover/visualize",
        "kafka",
        "mysql/dashboard",
        "mysql/lens",
        "nginx",
        "postgresql/duration",
        "postgresql/overview",
        "redis",
        "system/auth",
        "system/syslog/dashboard",
        "system/syslog/lens",
    ]
    for workflow in workflows:
        try:
            WorkflowSelectorParamSource(
                track=StaticTrack(),
                params={
                    "workflow": workflow,
                    "workflows-folder": "logs/workflows",
                    "task-offset": 0,
                },
            )
        except Exception as e:
            raise FailedWorkflowLoad(f"workflow {workflow} could not be loaded", e)


@pytest.mark.asyncio
async def test_workflow_selection():
    param_source = WorkflowSelectorParamSource(
        track=StaticTrack(parameters={"random-seed": 13, "number-of-workflows": 1}),
        params={
            "workflow": "a",
            "workflows-folder": "tests/parameter_sources/resources/workflows",
            "task-offset": 0,
        },
    )
    assert param_source.current_index == 0
    assert "5" in param_source.workflow_handlers
    assert "6" in param_source.workflow_handlers
    assert "51" in param_source.workflow_handlers
    assert "52" in param_source.workflow_handlers
    assert "61" in param_source.workflow_handlers
    # a
    assert param_source.workflows[0][0] == "5"
    assert param_source.workflows[0][1]["id"] == "5"
    assert param_source.workflows[1][0] == "6"
    assert param_source.workflows[2][0] == "51"
    assert param_source.workflows[3][0] == "52"
    assert param_source.workflows[4][0] == "61"

    param_source = param_source.partition(partition_index=0, total_partitions=1)
    # sequential consumption means this order should be predictable
    actions = ["5", "6", "51", "52", "61", "5", "6", "51", "52", "61"]
    for action_id in actions:
        action = param_source.params()
        assert action["id"] == action_id


@pytest.mark.asyncio
async def test_range_query_processing():
    clock = ReproducibleClock(
        start=datetime.datetime(year=2021, month=1, day=2, hour=12, minute=00, second=0)
    )
    param_source = WorkflowSelectorParamSource(
        track=StaticTrack(
            parameters={
                "query-max-date-start": "2020-09-30T00:00:00",
                "random-seed": 13,
                "number-of-workflows": 1,
            }
        ),
        params={
            "workflow": "a",
            "workflows-folder": "tests/parameter_sources/resources/workflows",
            "task-offset": 0,
        },
        utc_now=clock,
    )
    assert param_source.current_index == 0
    assert param_source.workflows[0][0] == "5"
    assert param_source.workflows[1][0] == "6"
    assert param_source.workflows[2][0] == "51"
    assert len(param_source.workflow_handlers["5"]) == 3
    assert param_source.workflow_handlers["5"][0].request_body == {
        "@timestamp": {
            "gte": "2020-11-30T12:16:59.340Z",
            "lte": "2020-12-01T12:16:59.340Z",
            "format": "strict_date_optional_time",
        }
    }
    assert param_source.workflow_handlers["5"][2].request_body == {
        "@timestamp": {
            "gte": "2020-11-30T11:16:59.340Z",
            "lte": "2020-12-01T11:16:59.340Z",
            "format": "strict_date_optional_time",
        }
    }

    assert param_source.workflow_handlers["5"][1].request_body == {
        "extended_bounds": {"max": 1606825019340, "min": 1606738619340},
        "field": "@timestamp",
        "fixed_interval": "10s",
        "min_doc_count": 0,
        "time_zone": "UTC",
    }

    assert len(param_source.workflow_handlers["6"]) == 1
    assert len(param_source.workflow_handlers["51"]) == 2

    param_source = param_source.partition(partition_index=0, total_partitions=1)
    # sequential consumption means this order should be predictable
    actions = ["5", "6", "51"]
    # shift our clock forward
    clock.increment(seconds=10)
    for action_id in actions:
        action = param_source.params()
        assert action["id"] == action_id
        # just check they are changed and difference is the same
        if action_id == "5":
            # test the RangeQueryHandler
            upper_bound = action["requests"][0]["stream"][0]["body"]["query"]["bool"][
                "must"
            ][0]["range"]["@timestamp"]["lte"]
            assert upper_bound == "2020-09-30T00:00:10.000Z"
            lower_bound = action["requests"][0]["stream"][0]["body"]["query"]["bool"][
                "must"
            ][0]["range"]["@timestamp"]["gte"]
            assert lower_bound == "2020-09-29T00:00:10.000Z"
            query_upper_bound = parse_date_optional_time(upper_bound).replace(
                tzinfo=datetime.timezone.utc
            )
            delta = query_upper_bound - parse_date_optional_time(lower_bound).replace(
                tzinfo=datetime.timezone.utc
            )
            assert delta.total_seconds() == 86400

            upper_bound = action["requests"][2]["body"]["query"]["range"]["@timestamp"][
                "lte"
            ]
            assert upper_bound == "2020-09-30T00:00:10.000Z"
            lower_bound = action["requests"][2]["body"]["query"]["range"]["@timestamp"][
                "gte"
            ]
            assert lower_bound == "2020-09-29T00:00:10.000Z"
            delta = parse_date_optional_time(upper_bound) - parse_date_optional_time(
                lower_bound
            )
            assert delta.total_seconds() == 86400
            # test the DateHistogram Handler
            upper_bound = action["requests"][0]["stream"][0]["body"]["aggs"][
                "log_level"
            ]["aggs"]["timeseries"]["date_histogram"]["extended_bounds"]["max"]
            lower_bound = action["requests"][0]["stream"][0]["body"]["aggs"][
                "log_level"
            ]["aggs"]["timeseries"]["date_histogram"]["extended_bounds"]["min"]
            assert lower_bound == 1601337610000
            assert upper_bound - lower_bound == 86400000
            # query_upper_bound should be the same as our upper bound
            assert upper_bound == int(query_upper_bound.timestamp() * 1000)


@pytest.mark.asyncio
async def test_complex_query():
    clock = ReproducibleClock(
        start=datetime.datetime(year=2021, month=1, day=2, hour=12, minute=00, second=0)
    )
    param_source = WorkflowSelectorParamSource(
        track=StaticTrack(
            parameters={
                "query-max-date-start": "2020-09-30T00:00:00",
                "random-seed": 13,
                "number-of-workflows": 1,
            }
        ),
        params={
            "workflow": "b",
            "workflows-folder": "tests/parameter_sources/resources/workflows",
            "task-offset": 0,
        },
        utc_now=clock,
    )
    assert param_source.current_index == 0
    assert "1" in param_source.workflow_handlers
    param_source = param_source.partition(partition_index=0, total_partitions=1)
    action = param_source.params()
    assert action["id"] == "1"
    assert len(param_source.workflow_handlers["1"]) == 2
    upper_bound = action["requests"][0]["stream"][0]["body"]["query"]["bool"]["filter"][
        2
    ]["range"]["@timestamp"]["lte"]
    assert upper_bound == "2020-09-30T00:00:00.000Z"
    lower_bound = action["requests"][0]["stream"][0]["body"]["query"]["bool"]["filter"][
        2
    ]["range"]["@timestamp"]["gte"]
    assert lower_bound == "2020-09-29T12:00:00.000Z"
    query_upper_bound = parse_date_optional_time(upper_bound).replace(
        tzinfo=datetime.timezone.utc
    )
    delta = query_upper_bound - parse_date_optional_time(lower_bound).replace(
        tzinfo=datetime.timezone.utc
    )
    assert delta.total_seconds() == 43200
    clock.increment(seconds=10)
    action = param_source.params()
    upper_bound = action["requests"][0]["body"]["query"]["range"]["@timestamp"]["lte"]
    assert upper_bound == "2020-09-30T00:00:10.000Z"


@pytest.mark.asyncio
async def test_complex_query_with_intervals():
    clock = ReproducibleClock(
        start=datetime.datetime(year=2021, month=1, day=2, hour=12, minute=00, second=0)
    )
    param_source = WorkflowSelectorParamSource(
        track=StaticTrack(
            parameters={
                "query-average-interval": "1h",
                "query-min-date": "2021-03-01",
                "query-max-date": "2021-03-02",
                "start-date": "2020-09-30T00:00:00",
                "random-seed": 13,
                "number-of-workflows": 1,
            }
        ),
        params={
            "seed": 13,
            "workflow": "b",
            "workflows-folder": "tests/parameter_sources/resources/workflows",
            "task-offset": 0,
        },
        utc_now=clock,
    )
    assert param_source.current_index == 0
    assert "1" in param_source.workflow_handlers
    param_source = param_source.partition(partition_index=0, total_partitions=1)
    action = param_source.params()
    assert action["id"] == "1"
    assert len(param_source.workflow_handlers["1"]) == 2
    upper_bound = action["requests"][0]["stream"][0]["body"]["query"]["bool"]["filter"][
        2
    ]["range"]["@timestamp"]["lte"]
    assert upper_bound == "2021-03-02T00:00:00.000Z"
    lower_bound = action["requests"][0]["stream"][0]["body"]["query"]["bool"]["filter"][
        2
    ]["range"]["@timestamp"]["gte"]
    assert lower_bound >= "2021-03-01T00:00:00.000Z"
    query_upper_bound = parse_date_optional_time(upper_bound).replace(
        tzinfo=datetime.timezone.utc
    )
    delta = query_upper_bound - parse_date_optional_time(lower_bound).replace(
        tzinfo=datetime.timezone.utc
    )
    # expect minimum delta to be enforced
    assert delta.total_seconds() >= 15 * 60


@pytest.mark.asyncio
async def test_average_query_duration_is_roughly_correct():
    clock = ReproducibleClock(
        start=datetime.datetime(year=2021, month=1, day=2, hour=12, minute=00, second=0)
    )
    deltas = []
    for _ in range(1000):
        param_source = WorkflowSelectorParamSource(
            track=StaticTrack(
                parameters={
                    "query-average-interval": "1h",
                    "query-min-date": "2021-03-01",
                    "query-max-date": "2021-03-02",
                    "start-date": "2020-09-30T00:00:00",
                    "random-seed": random.random(),
                    "number-of-workflows": 1,
                }
            ),
            params={
                "workflow": "b",
                "workflows-folder": "tests/parameter_sources/resources/workflows",
                "task-offset": 0,
            },
            utc_now=clock,
            min_query_duration=0,
        )
        assert param_source.current_index == 0
        assert "1" in param_source.workflow_handlers
        param_source = param_source.partition(partition_index=0, total_partitions=1)
        action = param_source.params()
        assert action["id"] == "1"
        assert len(param_source.workflow_handlers["1"]) == 2
        upper_bound = action["requests"][0]["stream"][0]["body"]["query"]["bool"][
            "filter"
        ][2]["range"]["@timestamp"]["lte"]
        assert upper_bound == "2021-03-02T00:00:00.000Z"
        lower_bound = action["requests"][0]["stream"][0]["body"]["query"]["bool"][
            "filter"
        ][2]["range"]["@timestamp"]["gte"]
        assert lower_bound >= "2021-03-01T00:00:00.000Z"
        query_upper_bound = parse_date_optional_time(upper_bound).replace(
            tzinfo=datetime.timezone.utc
        )
        delta = query_upper_bound - parse_date_optional_time(lower_bound).replace(
            tzinfo=datetime.timezone.utc
        )
        deltas.append(delta)
        action = param_source.params()
        # check a 2nd call produces the same value as only 2 queries with same range
        upper_bound = action["requests"][0]["body"]["query"]["range"]["@timestamp"][
            "lte"
        ]
        lower_bound = action["requests"][0]["body"]["query"]["range"]["@timestamp"][
            "gte"
        ]
        assert delta == parse_date_optional_time(upper_bound).replace(
            tzinfo=datetime.timezone.utc
        ) - parse_date_optional_time(lower_bound).replace(tzinfo=datetime.timezone.utc)
    # check override is intact
    assert min(deltas) < datetime.timedelta(minutes=15)
    # check rough average
    avg_actual_duration = sum([d.total_seconds() for d in deltas]) / len(deltas)
    assert (
        datetime.timedelta(minutes=55)
        < datetime.timedelta(seconds=avg_actual_duration)
        < datetime.timedelta(minutes=65)
    )


@pytest.mark.asyncio
def test_average_query_durations_are_scaled_to_max():
    clock = ReproducibleClock(
        start=datetime.datetime(year=2021, month=1, day=2, hour=12, minute=00, second=0)
    )
    # loop to increase randomness and cover more date permutations
    for i in range(1000):
        param_source = WorkflowSelectorParamSource(
            track=StaticTrack(
                parameters={
                    "query-average-interval": "1d",
                    "query-min-date": "2021-03-01",
                    "query-max-date": "2021-03-05",
                    "start-date": "2020-09-30T00:00:00",
                    "random-seed": 13,
                    "number-of-workflows": 1,
                }
            ),
            params={
                "workflow": "c",
                "workflows-folder": "tests/parameter_sources/resources/workflows",
                "task-offset": 0,
            },
            utc_now=clock,
            min_query_duration=0,
        )
        param_source = param_source.partition(partition_index=0, total_partitions=1)
        # action 2
        action = param_source.params()
        assert action["id"] == "2"
        assert len(param_source.workflow_handlers["2"]) == 3
        upper_bound = action["requests"][0]["stream"][0]["body"]["query"]["bool"][
            "must"
        ][0]["range"]["@timestamp"]["lte"]
        lower_bound = action["requests"][0]["stream"][0]["body"]["query"]["bool"][
            "must"
        ][0]["range"]["@timestamp"]["gte"]
        duration = parse_date_optional_time(upper_bound).replace(
            tzinfo=datetime.timezone.utc
        ) - parse_date_optional_time(lower_bound).replace(tzinfo=datetime.timezone.utc)
        # first query represents the max
        max_duration = duration.total_seconds()
        assert max_duration == param_source.max_query_duration
        upper_bound = action["requests"][0]["stream"][0]["body"]["aggs"]["log_level"][
            "aggs"
        ]["timeseries"]["date_histogram"]["extended_bounds"]["max"]
        lower_bound = action["requests"][0]["stream"][0]["body"]["aggs"]["log_level"][
            "aggs"
        ]["timeseries"]["date_histogram"]["extended_bounds"]["min"]
        duration = (upper_bound - lower_bound) / 1000
        assert duration == max_duration
        upper_bound = action["requests"][2]["body"]["query"]["range"]["@timestamp"][
            "lte"
        ]
        lower_bound = action["requests"][2]["body"]["query"]["range"]["@timestamp"][
            "gte"
        ]
        duration = parse_date_optional_time(upper_bound).replace(
            tzinfo=datetime.timezone.utc
        ) - parse_date_optional_time(lower_bound).replace(tzinfo=datetime.timezone.utc)
        assert duration.total_seconds() == max(
            ceil(max_duration * 0.75), param_source._min_query_duration
        )
        # action 3
        action = param_source.params()
        assert action["id"] == "3"
        assert len(param_source.workflow_handlers["3"]) == 1
        upper_bound = action["requests"][0]["body"]["query"]["range"]["@timestamp"][
            "lte"
        ]
        lower_bound = action["requests"][0]["body"]["query"]["range"]["@timestamp"][
            "gte"
        ]
        duration = parse_date_optional_time(upper_bound).replace(
            tzinfo=datetime.timezone.utc
        ) - parse_date_optional_time(lower_bound).replace(tzinfo=datetime.timezone.utc)
        assert duration.total_seconds() == max(
            ceil(max_duration * 0.5), param_source._min_query_duration
        )
        # action 4
        action = param_source.params()
        assert action["id"] == "4"
        assert len(param_source.workflow_handlers["4"]) == 2
        upper_bound = action["requests"][0]["body"]["query"]["range"]["@timestamp"][
            "lte"
        ]
        lower_bound = action["requests"][0]["body"]["query"]["range"]["@timestamp"][
            "gte"
        ]
        duration = parse_date_optional_time(upper_bound).replace(
            tzinfo=datetime.timezone.utc
        ) - parse_date_optional_time(lower_bound).replace(tzinfo=datetime.timezone.utc)
        assert duration.total_seconds() == max(
            ceil(max_duration * 0.25), param_source._min_query_duration
        )
        upper_bound = action["requests"][0]["body"]["aggs"]["log_level"]["aggs"][
            "timeseries"
        ]["date_histogram"]["extended_bounds"]["max"]
        lower_bound = action["requests"][0]["body"]["aggs"]["log_level"]["aggs"][
            "timeseries"
        ]["date_histogram"]["extended_bounds"]["min"]
        duration = (upper_bound - lower_bound) / 1000
        assert duration == max(
            ceil(max_duration * 0.25), param_source._min_query_duration
        )


@pytest.mark.asyncio
async def test_default_query_bounds_and_avg_interval():
    clock = ReproducibleClock(
        start=datetime.datetime(year=2021, month=1, day=2, hour=12, minute=00, second=0)
    )
    deltas = []
    for _ in range(1000):
        # this workflow has 1 query. It will always get the same value every time params() is called - since we scale
        # all queries in the workflow to 1 value (but we have only 1 value). We thus create many instances.
        param_source = WorkflowSelectorParamSource(
            track=StaticTrack(
                parameters={
                    "query-average-interval": "1d",
                    "random-seed": random.random(),
                    "number-of-workflows": 1,
                }
            ),
            params={
                "seed": 13,
                "workflow": "b",
                "workflows-folder": "tests/parameter_sources/resources/workflows",
                "task-offset": 0,
            },
            utc_now=clock,
            min_query_duration=0,
        )
        assert param_source.current_index == 0
        assert "1" in param_source.workflow_handlers
        param_source = param_source.partition(partition_index=0, total_partitions=1)
        action = param_source.params()
        assert action["id"] == "1"
        assert len(param_source.workflow_handlers["1"]) == 2
        upper_bound = action["requests"][0]["stream"][0]["body"]["query"]["bool"][
            "filter"
        ][2]["range"]["@timestamp"]["lte"]
        assert parse_date_optional_time(upper_bound) == parse_date_optional_time(
            DEFAULT_MAX_DATE
        )
        lower_bound = action["requests"][0]["stream"][0]["body"]["query"]["bool"][
            "filter"
        ][2]["range"]["@timestamp"]["gte"]
        query_upper_bound = parse_date_optional_time(upper_bound).replace(
            tzinfo=datetime.timezone.utc
        )
        delta = query_upper_bound - parse_date_optional_time(lower_bound).replace(
            tzinfo=datetime.timezone.utc
        )
        deltas.append(delta)
        action = param_source.params()
        # check a 2nd call produces the same value as only 2 queries with same range
        upper_bound = action["requests"][0]["body"]["query"]["range"]["@timestamp"][
            "lte"
        ]
        lower_bound = action["requests"][0]["body"]["query"]["range"]["@timestamp"][
            "gte"
        ]
        assert delta == parse_date_optional_time(upper_bound).replace(
            tzinfo=datetime.timezone.utc
        ) - parse_date_optional_time(lower_bound).replace(tzinfo=datetime.timezone.utc)
    # check override is intact
    assert min(deltas) < datetime.timedelta(minutes=15)
    # check rough average
    avg_actual_duration = sum([d.total_seconds() for d in deltas]) / len(deltas)
    assert (
        datetime.timedelta(hours=22)
        < datetime.timedelta(seconds=avg_actual_duration)
        < datetime.timedelta(hours=26)
    )


@pytest.mark.asyncio
async def test_invalid_min_max():
    clock = ReproducibleClock(
        start=datetime.datetime(year=2021, month=1, day=2, hour=12, minute=00, second=0)
    )
    param_source = WorkflowSelectorParamSource(
        track=StaticTrack(
            parameters={
                "query-min-date": "2020-01-02",
                "query_max-date": "2020-01-01",
                "query-average-interval": "1d",
            }
        ),
        params={
            "workflow": "b",
            "workflows-folder": "tests/parameter_sources/resources/workflows",
        },
        utc_now=clock,
        min_query_duration=0,
    )

    with pytest.raises(TrackConfigError) as err:
        param_source.params()
    assert (
        err.value.message
        == "query-min-date 2020-01-02 00:00:00+00:00 cannot be larger than effective "
        "query-max-date 2020-01-01 00:00:00+00:00"
    )


@pytest.mark.asyncio
async def test_invalid_min_max():
    clock = ReproducibleClock(
        start=datetime.datetime(year=2021, month=1, day=2, hour=12, minute=00, second=0)
    )
    param_source = WorkflowSelectorParamSource(
        track=StaticTrack(
            parameters={
                "query-min-date": "2020-01-02",
                "query_max-date-start": "2020-01-01",
                "query-average-interval": "1d",
                "number-of-workflows": 1,
            }
        ),
        params={
            "workflow": "b",
            "workflows-folder": "tests/parameter_sources/resources/workflows",
            "task-offset": 0,
        },
        utc_now=clock,
        min_query_duration=0,
    )

    with pytest.raises(TrackConfigError) as err:
        param_source.params()
    assert (
        err.value.message
        == "query-min-date 2020-01-02 00:00:00+00:00 cannot be larger than effective "
        "query-max-date 2020-01-01 00:00:00+00:00"
    )


@pytest.mark.asyncio
async def test_no_workflows():
    with pytest.raises(TrackConfigError) as rae:
        WorkflowSelectorParamSource(
            track=StaticTrack(),
            params={
                "workflow": "a",
                "workflows-folder": "./workflows-2",
            },
        )
    assert (
        rae.value.message
        == "No actions loaded. [./workflows-2] contains no action files"
    )


@pytest.mark.asyncio
async def test_invalid_missing_requests_key():
    with pytest.raises(TrackConfigError) as rae:
        WorkflowSelectorParamSource(
            track=StaticTrack(),
            params={
                "workflow": "missing_requests",
                "workflows-folder": "tests/parameter_sources/resources/invalid_workflows",
                "task-offset": 0,
            },
        )
    assert re.match(
        r"^Action \[.*/tests/parameter_sources/resources/invalid_workflows/missing_requests/sample.json\] for "
        r"\[missing_requests\] is missing a \"requests\" key",
        rae.value.message,
    )


@pytest.mark.asyncio
async def test_invalid_missing_requests_id():
    with pytest.raises(TrackConfigError) as rae:
        WorkflowSelectorParamSource(
            track=StaticTrack(),
            params={
                "workflow": "missing_id",
                "workflows-folder": "tests/parameter_sources/resources/invalid_workflows",
                "task-offset": 0,
            },
        )
    assert re.match(
        r"^Action \[.*/tests/parameter_sources/resources/invalid_workflows/missing_id/sample.json\] for "
        r"\[missing_id\] is missing an \"id\" key",
        rae.value.message,
    )


@pytest.mark.asyncio
async def test_duplicate_action_id():
    with pytest.raises(TrackConfigError) as rae:
        WorkflowSelectorParamSource(
            track=StaticTrack(),
            params={
                "workflow": "duplicate_action_ids",
                "workflows-folder": "tests/parameter_sources/resources/invalid_workflows",
                "task-offset": 0,
            },
        )
    assert (
        rae.value.message
        == "Action id [1] for [duplicate_action_ids] is duplicated. This must be unique"
    )


@pytest.mark.asyncio
async def test_no_workflows():
    with pytest.raises(DataError) as rae:
        WorkflowSelectorParamSource(
            track=StaticTrack(),
            params={"workflows": "../tests/parameter_sources/resources/request_sets"},
        )
    assert (
        rae.value.message
        == "Parameter source for operation 'composite' did not provide the mandatory parameter "
        "'workflow'. Add it to your parameter source and try again."
    )


@pytest.mark.asyncio
async def test_detailed_results():
    param_source = WorkflowSelectorParamSource(
        track=StaticTrack(parameters={"detailed-results": True}),
        params={
            "workflow": "a",
            "workflows-folder": "tests/parameter_sources/resources/workflows",
            "task-offset": 0,
        },
    )
    assert param_source.workflows[0][0] == "5"
    assert (
        "detailed-results" in param_source.workflows[0][1]["requests"][0]["stream"][0]
    )
    # all workflows in workflows/a are identical
    for i in range(5):
        assert param_source.workflows[i][1]["requests"][0]["stream"][0][
            "detailed-results"
        ]
        assert param_source.workflows[i][1]["requests"][1]["stream"][0][
            "detailed-results"
        ]
        assert param_source.workflows[i][1]["requests"][2]["detailed-results"]


def test_seeding():
    seed = 15
    param_source = WorkflowSelectorParamSource(
        track=StaticTrack(
            parameters={
                "detailed-results": True,
                "random-seed": seed,
                "number-of-workflows": 2,
            }
        ),
        params={
            "workflow": "a",
            "workflows-folder": "tests/parameter_sources/resources/workflows",
            "task-offset": 0,
        },
    )
    param_source = param_source.partition(partition_index=3, total_partitions=4)
    # 10000 * ((num_workflows * (partition_index+1)) + (task_id+1) + random_seed)
    # 10000 * ((2 * 4) + 1 + 15) = 240000
    assert param_source.random_seed == 240000


def test_request_params():
    param_source = WorkflowSelectorParamSource(
        track=StaticTrack(
            parameters={"query-average-interval": "1d", "random-seed": 13}
        ),
        params={
            "seed": 13,
            "workflow": "b",
            "workflows-folder": "tests/parameter_sources/resources/workflows",
            "request-params": {"request_cache": True},
            "task-offset": 0,
        },
        min_query_duration=0,
    )
    assert param_source.workflows[0][0] == "1"
    assert param_source.workflows[0][1]["requests"][0]["stream"][0]["request-params"][
        "request_cache"
    ]
    assert (
        len(param_source.workflows[0][1]["requests"][0]["stream"][0]["request-params"])
        == 1
    )
    assert (
        len(param_source.workflows[0][1]["requests"][0]["stream"][1]["request-params"])
        == 3
    )
    assert (
        param_source.workflows[0][1]["requests"][0]["stream"][1]["request-params"][
            "track_total_hits"
        ]
        == 1000
    )
    assert not param_source.workflows[0][1]["requests"][0]["stream"][1][
        "request-params"
    ]["track_scores"]
    assert param_source.workflows[0][1]["requests"][0]["stream"][1]["request-params"][
        "request_cache"
    ]
    assert param_source.workflows[0][1]["requests"][0]["stream"][2][
        "request-params"
    ] == {"request_cache": "true"}


def test_stringify_bool():
    parameters = {"request_cache": True, "search_type": "query_then_fetch"}
    WorkflowSelectorParamSource.stringify_bool(parameters)
    assert parameters["request_cache"] == "true"
    assert parameters["search_type"] == "query_then_fetch"

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
import pytest
from esrally.exceptions import TrackConfigError

from shared.utils.time import DateTimeValues, TimeParsingError
from shared.query_handlers import RangeQueryHandler


def test_process_inclusive():
    max = datetime.datetime(year=2020, month=12, day=2, hour=12, minute=33, second=0)
    range_query = {
        "@timestamp": {
            "gte": "2020-11-30T12:16:59.340Z",
            "lte": "2020-12-01T12:16:59.340Z",
            "format": "strict_date_optional_time",
        }
    }
    range_query_handler = RangeQueryHandler(range_query)
    range_query_handler.process(
        DateTimeValues(max_date=max, min_date=None, duration=None)
    )
    assert range_query["@timestamp"]["gte"] == "2020-12-01T12:33:00.000Z"
    assert range_query["@timestamp"]["lte"] == "2020-12-02T12:33:00.000Z"


def test_process_expand_bounds():
    max = datetime.datetime(year=2020, month=12, day=2, hour=12, minute=33, second=0)
    range_query = {
        "@timestamp": {
            "gte": "2020-11-30T12:16:59.340Z",
            "lte": "2020-12-01T12:16:59.340Z",
            "format": "strict_date_optional_time",
        }
    }
    range_query_handler = RangeQueryHandler(range_query)
    duration = datetime.timedelta(days=5)
    range_query_handler.process(
        DateTimeValues(min_date=None, max_date=max, duration=duration)
    )
    assert range_query["@timestamp"]["gte"] == "2020-11-27T12:33:00.000Z"
    assert range_query["@timestamp"]["lte"] == "2020-12-02T12:33:00.000Z"


def test_process_contract_bounds_with_min_date():
    min = datetime.datetime(year=2020, month=12, day=2, hour=11, minute=33, second=0)
    max = datetime.datetime(year=2020, month=12, day=2, hour=12, minute=33, second=0)
    range_query = {
        "@timestamp": {
            "gte": "2020-11-30T12:16:59.340Z",
            "lte": "2020-12-01T12:16:59.340Z",
            "format": "strict_date_optional_time",
        }
    }
    range_query_handler = RangeQueryHandler(range_query)
    range_query_handler.process(
        DateTimeValues(max_date=max, min_date=min, duration=None)
    )
    assert range_query["@timestamp"]["gte"] == "2020-12-02T11:33:00.000Z"
    assert range_query["@timestamp"]["lte"] == "2020-12-02T12:33:00.000Z"


def test_process_contract_bounds_with_duration():
    max = datetime.datetime(year=2020, month=12, day=2, hour=12, minute=33, second=0)
    range_query = {
        "@timestamp": {
            "gte": "2020-11-30T12:16:59.340Z",
            "lte": "2020-12-01T12:16:59.340Z",
            "format": "strict_date_optional_time",
        }
    }
    range_query_handler = RangeQueryHandler(range_query)
    duration = datetime.timedelta(hours=1)
    range_query_handler.process(
        DateTimeValues(max_date=max, min_date=None, duration=duration)
    )
    assert range_query["@timestamp"]["gte"] == "2020-12-02T11:33:00.000Z"
    assert range_query["@timestamp"]["lte"] == "2020-12-02T12:33:00.000Z"


def test_process_exclusive():
    max = datetime.datetime(year=2020, month=12, day=2, hour=12, minute=33, second=0)
    range_query = {
        "@timestamp": {
            "gt": "2020-11-30T12:16:59.340Z",
            "lt": "2020-12-01T12:16:59.340Z",
            "format": "strict_date_optional_time",
        }
    }
    range_query_handler = RangeQueryHandler(range_query)
    range_query_handler.process(
        DateTimeValues(max_date=max, min_date=None, duration=None)
    )
    assert range_query["@timestamp"]["gt"] == "2020-12-01T12:33:00.000Z"
    assert range_query["@timestamp"]["lt"] == "2020-12-02T12:33:00.000Z"


def test_process_with_dates():
    max = datetime.datetime(year=2020, month=12, day=2)
    range_query = {
        "@timestamp": {
            "gte": "2020-11-30",
            "lte": "2020-12-01",
            "format": "strict_date_optional_time",
        }
    }
    range_query_handler = RangeQueryHandler(range_query)
    range_query_handler.process(
        DateTimeValues(max_date=max, min_date=None, duration=None)
    )
    assert range_query["@timestamp"]["gte"] == "2020-12-01T00:00:00.000Z"
    assert range_query["@timestamp"]["lte"] == "2020-12-02T00:00:00.000Z"


def test_invalid_time_date():
    with pytest.raises(TimeParsingError) as rae:
        RangeQueryHandler(
            {
                "@timestamp": {
                    "gte": "2020-11-30T:16:59.340Z",
                    "lte": "2020-12-01T12:16:59.340Z",
                    "format": "strict_date_optional_time",
                }
            }
        ).process(
            DateTimeValues(
                min_date=None, max_date=datetime.datetime.utcnow(), duration=None
            )
        )
    assert rae.value.args[0] == "Invalid time format: 2020-11-30T:16:59.340Z"


def test_missing_gte():
    with pytest.raises(TrackConfigError) as rae:
        RangeQueryHandler(
            {
                "@timestamp": {
                    "lte": "2020-12-01T12:16:59.340Z",
                    "format": "strict_date_optional_time",
                }
            }
        ).process(
            DateTimeValues(
                min_date=None, max_date=datetime.datetime.utcnow(), duration=None
            )
        )
    assert (
        rae.value.message
        == 'Range query for date does not have both "gte" or "gt" and '
        "\"lte\" or \"lt\" key - [{'@timestamp': {'lte': '2020-12-01T12:16:59.340Z', "
        "'format': 'strict_date_optional_time'}}]"
    )


def test_missing_lte():
    with pytest.raises(TrackConfigError) as rae:
        RangeQueryHandler(
            {
                "@timestamp": {
                    "gte": "2020-12-01T12:16:59.340Z",
                    "format": "strict_date_optional_time",
                }
            }
        ).process(
            DateTimeValues(
                min_date=None, max_date=datetime.datetime.utcnow(), duration=None
            )
        )
    assert (
        rae.value.message
        == 'Range query for date does not have both "gte" or "gt" and '
        "\"lte\" or \"lt\" key - [{'@timestamp': {'gte': '2020-12-01T12:16:59.340Z', "
        "'format': 'strict_date_optional_time'}}]"
    )


def test_pass_through():
    range_query = {"http.status.code": {"gte": 200, "lte": 300}}
    range_query_handler = RangeQueryHandler(range_query)
    range_query_handler.process(
        DateTimeValues(
            min_date=None, max_date=datetime.datetime.utcnow(), duration=None
        )
    )
    assert range_query["http.status.code"]["gte"] == 200
    assert range_query["http.status.code"]["lte"] == 300


def test_get_time_interval():
    range_query = {
        "@timestamp": {
            "gte": "2020-11-30T12:16:59.340Z",
            "lte": "2020-12-01T12:16:59.340Z",
            "format": "strict_date_optional_time",
        }
    }
    range_query_handler = RangeQueryHandler(range_query)
    time_interval = range_query_handler.get_time_interval()
    assert time_interval.total_seconds() == 86400


def test_get_time_interval_is_idempotent():
    max = datetime.datetime(year=2020, month=12, day=2, hour=12, minute=33, second=0)
    range_query = {
        "@timestamp": {
            "gte": "2020-11-30T12:16:59.340Z",
            "lte": "2020-12-01T12:16:59.340Z",
            "format": "strict_date_optional_time",
        }
    }
    range_query_handler = RangeQueryHandler(range_query)
    time_interval = range_query_handler.get_time_interval()
    range_query_handler.process(
        DateTimeValues(max_date=max, min_date=None, duration=None)
    )
    assert time_interval == range_query_handler.get_time_interval()

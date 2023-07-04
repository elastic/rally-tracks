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
from shared.utils.time import (
    DateTimeValues,
    TimeParsingError,
    TimestampStructGenerator,
    parse_date_optional_time,
    parse_date_time,
)


class ReproducibleClock:
    def __init__(self, start):
        self.now = start

    def __call__(self, *args, **kwargs):
        return self.now


def test_generate_from_now():
    clock = ReproducibleClock(start=datetime.datetime(year=2019, month=1, day=5, hour=15))

    g = TimestampStructGenerator(starting_point=clock.now)

    assert g.next(datetime.timedelta(seconds=5)) == datetime.datetime(year=2019, month=1, day=5, hour=15, minute=0, second=5)

    assert g.next(datetime.timedelta(seconds=10)) == datetime.datetime(year=2019, month=1, day=5, hour=15, minute=0, second=15)

    assert g.next(datetime.timedelta(seconds=2)) == datetime.datetime(year=2019, month=1, day=5, hour=15, minute=0, second=17)


def test_parse_date_time():
    date_time = parse_date_time("2018-05-01T00:59:56Z")
    assert date_time == datetime.datetime(
        year=2018,
        month=5,
        day=1,
        hour=0,
        minute=59,
        second=56,
        tzinfo=datetime.timezone.utc,
    )


def test_parse_date_time_no_separator():
    date_time = parse_date_time("2018-05-01:00:59:56")
    assert date_time == datetime.datetime(
        year=2018,
        month=5,
        day=1,
        hour=0,
        minute=59,
        second=56,
        tzinfo=datetime.timezone.utc,
    )


def test_parse_date():
    date = parse_date_time("2018-05-01")
    assert date == datetime.datetime(year=2018, month=5, day=1, hour=0, minute=0, tzinfo=datetime.timezone.utc)


def test_parse_now():
    clock = ReproducibleClock(start=datetime.datetime(year=2019, month=1, day=5, hour=15, tzinfo=datetime.timezone.utc))
    date = parse_date_time("now", utcnow=clock)
    assert date == datetime.datetime(year=2019, month=1, day=5, hour=15, tzinfo=datetime.timezone.utc)


def test_parse_relative_day():
    clock = ReproducibleClock(start=datetime.datetime(year=2019, month=1, day=5, hour=15, tzinfo=datetime.timezone.utc))
    date = parse_date_time("now+1d", utcnow=clock)
    assert date == datetime.datetime(year=2019, month=1, day=6, hour=15, tzinfo=datetime.timezone.utc)


def test_parse_relative_minus_day():
    clock = ReproducibleClock(start=datetime.datetime(year=2019, month=1, day=5, hour=15, tzinfo=datetime.timezone.utc))
    date = parse_date_time("now-1d", utcnow=clock)
    assert date == datetime.datetime(year=2019, month=1, day=4, hour=15, tzinfo=datetime.timezone.utc)


def test_parse_relative_hour():
    clock = ReproducibleClock(start=datetime.datetime(year=2019, month=1, day=5, hour=15, tzinfo=datetime.timezone.utc))
    date = parse_date_time("now+1h", utcnow=clock)
    assert date == datetime.datetime(year=2019, month=1, day=5, hour=16, tzinfo=datetime.timezone.utc)


def test_parse_relative_minus_hour():
    clock = ReproducibleClock(start=datetime.datetime(year=2019, month=1, day=5, hour=15, tzinfo=datetime.timezone.utc))
    date = parse_date_time("now-1h", utcnow=clock)
    assert date == datetime.datetime(year=2019, month=1, day=5, hour=14, tzinfo=datetime.timezone.utc)


def test_parse_relative_minute():
    clock = ReproducibleClock(start=datetime.datetime(year=2019, month=1, day=5, hour=15, minute=30, tzinfo=datetime.timezone.utc))
    date = parse_date_time("now+30m", utcnow=clock)
    assert date == datetime.datetime(year=2019, month=1, day=5, hour=16, tzinfo=datetime.timezone.utc)


def test_parse_relative_minus_minute():
    clock = ReproducibleClock(start=datetime.datetime(year=2019, month=1, day=5, hour=14, minute=30, tzinfo=datetime.timezone.utc))
    date = parse_date_time("now-30m", utcnow=clock)
    assert date == datetime.datetime(year=2019, month=1, day=5, hour=14, tzinfo=datetime.timezone.utc)


def test_parse_invalid_offset():
    # "w" is unsupported
    with pytest.raises(TimeParsingError) as ex:
        parse_date_time("now+1w")
    assert "Invalid offset: +1w" == str(ex.value)


def test_parse_invalid_time():
    # "w" is unsupported
    with pytest.raises(TimeParsingError) as ex:
        parse_date_time("monday+1d")
    assert "Invalid time format: monday+1d" == str(ex.value)


def test_generate_new_bounds_preserve_interval():
    upper_bound = parse_date_optional_time("2020-01-03T12:00:00.000Z")
    lower_bound = parse_date_optional_time("2020-01-02T12:00:00.000Z")

    utc_now = datetime.datetime.utcnow()
    date_data = DateTimeValues(min_date=None, max_date=utc_now, duration=None)

    new_lower, new_upper = date_data.generate_new_bounds(lower_bound, upper_bound)
    assert (new_upper - new_lower) == (upper_bound - lower_bound)
    assert new_upper != upper_bound
    assert new_lower != lower_bound


def test_generate_new_bounds_replace_interval():
    upper_bound = parse_date_optional_time("2020-01-03T12:00:00.000Z")
    lower_bound = parse_date_optional_time("2020-01-02T12:00:00.000Z")

    utc_now = datetime.datetime.utcnow()
    date_data = DateTimeValues(min_date=None, max_date=utc_now, duration=datetime.timedelta(minutes=1))

    new_lower, new_upper = date_data.generate_new_bounds(lower_bound, upper_bound)
    assert (new_upper - new_lower) == datetime.timedelta(minutes=1)


def test_generate_new_bounds_respects_min_and_max_date():
    """
    If query_max_date - query_min_date > interval, just use query_min_date and query_max_date
    """
    query_min_date = parse_date_optional_time("2021-01-01T12:00:00.000Z")
    query_max_date = parse_date_optional_time("2021-01-01T12:01:00.000Z")
    interval = datetime.timedelta(minutes=5)
    date_data = DateTimeValues(min_date=query_min_date, max_date=query_max_date, duration=interval)
    new_lower, new_upper = date_data.generate_new_bounds(None, None)
    assert query_min_date == new_lower
    assert query_max_date == new_upper


def test_calendar_intervals():
    utc_now = datetime.datetime.utcnow()
    date_data = DateTimeValues(None, utc_now, None)
    assert date_data.calendar_interval is None

    date_data = DateTimeValues(None, utc_now, datetime.timedelta(days=365))
    assert date_data.calendar_interval == "week"

    date_data = DateTimeValues(None, utc_now, datetime.timedelta(days=7))
    assert date_data.calendar_interval == "day"

    date_data = DateTimeValues(None, utc_now, datetime.timedelta(minutes=15))
    assert date_data.calendar_interval == "minute"


def test_fixed_intervals():
    utc_now = datetime.datetime.utcnow()
    date_data = DateTimeValues(None, utc_now, None)
    assert date_data.calendar_interval is None

    date_data = DateTimeValues(None, utc_now, datetime.timedelta(days=365))
    assert date_data.fixed_interval == "1d"

    date_data = DateTimeValues(None, utc_now, datetime.timedelta(days=1))
    assert date_data.fixed_interval == "10m"

    date_data = DateTimeValues(None, utc_now, datetime.timedelta(minutes=15))
    assert date_data.fixed_interval == "10s"

    date_data = DateTimeValues(None, utc_now, datetime.timedelta(days=100))
    assert date_data.fixed_interval == "1d"

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
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import random
import re
from functools import cached_property
from typing import Callable, Optional, Any

from esrally import exceptions


class TimeParsingError(Exception):
    """Exception raised for parameter parsing errors.
    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message


class TimestampStructGenerator:
    def __init__(self, starting_point):
        self._starting_point = starting_point

    def utcnow(self):
        # datetime.datetime.utcnow is not tz aware
        return datetime.now(timezone.utc)

    def next(self, delta):
        self._starting_point = self._starting_point + delta
        return self._starting_point


def random_duration_for_max(
    average_duration: int, min_seconds: int, max_seconds: int
) -> Optional[int]:
    if average_duration:
        result = int(random.expovariate(1 / average_duration.total_seconds()))
        # enforce minimum delta for realistic workloads
        if result >= min_seconds:
            if result < max_seconds:
                return result
            return max_seconds
        return min_seconds
    return None


def parse_interval(offset: str) -> Optional[timedelta]:
    if not offset:
        return None
    match = re.match(r"^([+-]?\d+)([hmd])$", offset)
    if match:
        offset_amount = int(match.group(1))
        if match.group(2) == "m":
            return timedelta(minutes=offset_amount)
        elif match.group(2) == "h":
            return timedelta(hours=offset_amount)
        elif match.group(2) == "d":
            return timedelta(days=offset_amount)
        else:
            raise TimeParsingError(f"Invalid offset: {offset}")
    else:
        raise TimeParsingError(f"Invalid offset: {offset}")


def parse_date_time(
    point: str, utcnow: Callable[..., datetime] = datetime.utcnow
) -> Optional[datetime]:
    now = "now"
    if not point:
        return None
    elif point == now:
        return utcnow()
    elif point.startswith(now):
        return utcnow() + parse_interval(point[len(now) :])
    else:
        return parse_date_optional_time(point)


def parse_date_optional_time(date_time: str):
    match = re.match(
        r"^(\d{4})\D(\d{2})\D(\d{2})\D(\d{2})\D(\d{2})\D(\d{2})(?:\.\d{0,3})?Z?$",
        date_time,
    )
    if match:
        return datetime(
            year=int(match.group(1)),
            month=int(match.group(2)),
            day=int(match.group(3)),
            hour=int(match.group(4)),
            minute=int(match.group(5)),
            second=int(match.group(6)),
            tzinfo=timezone.utc,
        )
    else:
        match = re.match(r"^(\d{4})\D(\d{2})\D(\d{2})$", date_time)
        if match:
            return datetime(
                year=int(match.group(1)),
                month=int(match.group(2)),
                day=int(match.group(3)),
                tzinfo=timezone.utc,
            )
    raise TimeParsingError(f"Invalid time format: {date_time}")


@dataclass
class DateTimeValues:
    """
    Keeps configured/parsed date data from track, workflow, and corpora sources and is responsible for providing
    appropriate bounds and intervals for usage of live queries.
    """

    min_date: Optional[datetime]
    max_date: datetime
    duration: Optional[timedelta]
    lower: Optional[datetime] = field(default=None, init=False)

    def generate_new_bounds(self, lower_bound, upper_bound):
        """
        Returns a tuple of (min: datetime, max: datetime) that represent what the action should be querying on.
        Always returns the initial max_date value as the max.
        If a duration was specified at initialization, min = max - self.duration.
        By default duration is preserved from original action.
        :param lower_bound: datetime from original action, parsed from range.timestamp.gt(e) or extended_bounds.min.
        :param upper_bound: datetime from original action, parsed from range.timestamp.lt(e) or extended_bounds.max.
        """
        if self.min_date and self.min_date > self.max_date:
            raise exceptions.TrackConfigError(
                f"query-min-date {self.min_date} "
                f"cannot be larger than effective query-max-date {self.max_date}"
            )
        if not self.duration:
            self.duration = upper_bound - lower_bound
        if self.min_date:
            self.lower = max(self.min_date, self.max_date - self.duration)
        else:
            self.lower = self.max_date - self.duration
        return self.lower, self.max_date

    # interval properties roughly mimic Kibana logic, as of 7.11.2:
    # https://github.com/elastic/kibana/blob/v7.11.2/src/plugins/data/common/search/aggs/buckets/lib/time_buckets/calc_auto_interval.ts
    # requires self.duration to be initialized at object creation or from invocation of generate_new_bounds(), otherwise
    # returns None, at which point consumer should preserve any existing calendar_interval setting.
    @cached_property
    def calendar_interval(self):
        if self.duration is None:
            return None
        target = self.duration / 100
        if target > timedelta(days=93):
            return "year"
        elif target > timedelta(days=28):
            return "quarter"
        elif target > timedelta(days=7):
            return "month"
        elif target > timedelta(days=1):
            return "week"
        elif target > timedelta(hours=1):
            return "day"
        elif target > timedelta(minutes=1):
            return "hour"
        return "minute"

    # interval properties roughly mimic Kibana logic, as of 7.11.2:
    # https://github.com/elastic/kibana/blob/v7.11.2/src/plugins/data/common/search/aggs/buckets/lib/time_buckets/calc_auto_interval.ts
    # requires self.duration to be initialized at object creation or from invocation of generate_new_bounds(), otherwise
    # returns None, at which point consumer should preserve any existing fixed_interval setting.
    @cached_property
    def fixed_interval(self):
        if self.duration is None:
            return None
        target = self.duration / 100
        if target >= timedelta(days=365):
            return "365d"
        elif target >= timedelta(days=21):
            return "30d"
        elif target >= timedelta(days=7):
            return "7d"
        elif target >= timedelta(days=1):
            return "1d"
        elif target >= timedelta(hours=6):
            return "12h"
        elif target >= timedelta(hours=2):
            return "2h"
        elif target >= timedelta(minutes=45):
            return "1h"
        elif target >= timedelta(minutes=20):
            return "30m"
        elif target >= timedelta(minutes=9):
            return "10m"
        elif target >= timedelta(minutes=3):
            return "5m"
        elif target >= timedelta(seconds=45):
            return "1m"
        elif target >= timedelta(seconds=15):
            return "30s"
        return "10s"

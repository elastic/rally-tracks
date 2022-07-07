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

from shared.ts_generators import FixedIntervalGenerator


def test_generate_from_now():
    start_date = datetime.datetime(
        year=2019, month=1, day=5, hour=15, tzinfo=datetime.timezone.utc
    )
    random.seed(13)
    generator = FixedIntervalGenerator(8640000, start_date, 1)
    assert (
        generator.next_timestamp().isoformat(sep="T", timespec="milliseconds")
        == "2019-01-05T15:00:00.007+00:00"
    )
    assert (
        generator.next_timestamp().isoformat(sep="T", timespec="milliseconds")
        == "2019-01-05T15:00:00.017+00:00"
    )
    assert (
        generator.next_timestamp().isoformat(sep="T", timespec="milliseconds")
        == "2019-01-05T15:00:00.027+00:00"
    )


def test_generate_from_now_multiple_clients():
    start_date = datetime.datetime(
        year=2019, month=1, day=5, hour=15, tzinfo=datetime.timezone.utc
    )
    random.seed(13)
    generator = FixedIntervalGenerator(8640000, start_date, 2)
    assert (
        generator.next_timestamp().isoformat(sep="T", timespec="milliseconds")
        == "2019-01-05T15:00:00.014+00:00"
    )
    assert (
        generator.next_timestamp().isoformat(sep="T", timespec="milliseconds")
        == "2019-01-05T15:00:00.034+00:00"
    )
    assert (
        generator.next_timestamp().isoformat(sep="T", timespec="milliseconds")
        == "2019-01-05T15:00:00.054+00:00"
    )

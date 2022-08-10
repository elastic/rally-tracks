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

import time
from datetime import datetime
import pytest

# This benchmark was used to test implementations of time formatting in ProcessedCorpusParamSource._json_processor() after it was determined
# time.strftime() behaved unexpectedly with format input of '%s'

TEST_DATETIME = datetime.strptime("2020-08-31T04:12:26.435Z", "%Y-%m-%dT%H:%M:%S.%fZ")


@pytest.mark.benchmark(
    group="parse",
    warmup="on",
    warmup_iterations=10000,
    disable_gc=True,
)
def test_correct_epoch(benchmark):
    benchmark(parse_with_branch, "%s", TEST_DATETIME)


@pytest.mark.benchmark(
    group="parse",
    warmup="on",
    warmup_iterations=10000,
    disable_gc=True,
)
def test_incorrect_epoch(benchmark):
    benchmark(parse_with_strftime, "%s", TEST_DATETIME)


@pytest.mark.benchmark(
    group="parse",
    warmup="on",
    warmup_iterations=10000,
    disable_gc=True,
)
def test_branching_isostring(benchmark):
    benchmark(parse_with_branch, "%d/%b/%Y:%H:%M:%S +0000", TEST_DATETIME)


@pytest.mark.benchmark(
    group="parse",
    warmup="on",
    warmup_iterations=10000,
    disable_gc=True,
)
def test_original_isostring(benchmark):
    benchmark(parse_with_strftime, "%d/%b/%Y:%H:%M:%S +0000", TEST_DATETIME)


def parse_with_branch(ts_format, timestamp):
    if ts_format == "%s":
        formatted_ts = timestamp.timestamp().__trunc__()
    else:
        formatted_ts = time.strftime(ts_format, timestamp.timetuple())
    return formatted_ts


def parse_with_strftime(ts_format, timestamp):
    return time.strftime(ts_format, timestamp.timetuple())

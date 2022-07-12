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

import random
from datetime import timedelta

from shared.ts_generators.generator import Generator

MILLISECONDS_PER_DAY = 86400000


class FixedIntervalGenerator(Generator):
    def __init__(self, mean_docs_per_day, start_date, clients, **kwargs):
        super().__init__(mean_docs_per_day, start_date, clients, **kwargs)
        self._doc_per_milli = MILLISECONDS_PER_DAY / (mean_docs_per_day / clients)
        # subtract some uniform variance for the current time so not all clients are aligned
        self._timestamp_generator.next(
            timedelta(milliseconds=-random.uniform(0, self._doc_per_milli))
        )
        self._wait_time = (clients / mean_docs_per_day) * MILLISECONDS_PER_DAY

    def next_timestamp(self):
        # there are faster ways to do this but currently this is used in generation
        # and isn't expected to be the bottleneck
        return self._timestamp_generator.next(timedelta(milliseconds=self._wait_time))

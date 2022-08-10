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

from enum import Enum
from esrally import exceptions

from shared.ts_generators.fixed_interval import FixedIntervalGenerator

__TS_GENERATORS = {}


class ProfileType(Enum):
    Fixed_Interval = 1


def register_profiles(profiler_type, generator):
    __TS_GENERATORS[profiler_type] = generator


def get_ts_generator(profile_type, mean_docs_per_day, start_date, clients, **kwargs):
    if profile_type in __TS_GENERATORS:
        return __TS_GENERATORS[profile_type](
            mean_docs_per_day, start_date, clients, **kwargs
        )
    else:
        raise exceptions.TrackConfigError(
            f"[{profile_type}] is not a registered profile"
        )


register_profiles(ProfileType.Fixed_Interval.name.lower(), FixedIntervalGenerator)

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
from esrally import exceptions

from shared.utils.time import parse_date_optional_time


class RangeQueryHandler:
    def __init__(self, request_body):
        self.request_body = request_body
        self.upper_bound = None
        self.upper_inclusive = True
        self.lower_bound = None
        self.lower_inclusive = True
        self.read_ranges()

    def read_ranges(self):
        fields = list(self.request_body.keys())
        if len(fields) == 1:
            self.query_range = self.request_body[fields[0]]
            # we require date queries to use strict_date_optional_time vs trying to figure out the format
            if (
                "format" in self.query_range
                and self.query_range["format"] == "strict_date_optional_time"
            ):
                if "gte" in self.query_range:
                    self.lower_bound = parse_date_optional_time(self.query_range["gte"])
                elif "gt" in self.query_range:
                    self.lower_bound = parse_date_optional_time(self.query_range["gt"])
                    self.lower_inclusive = False
                if "lte" in self.query_range:
                    self.upper_bound = parse_date_optional_time(self.query_range["lte"])
                elif "lt" in self.query_range:
                    self.upper_bound = parse_date_optional_time(self.query_range["lt"])
                    self.upper_inclusive = False
                if not self.upper_bound or not self.lower_bound:
                    raise exceptions.TrackConfigError(
                        f'Range query for date does not have both "gte" or "gt" '
                        f'and "lte" or "lt" key - [{self.request_body}]'
                    )
        else:
            raise exceptions.TrackConfigError(
                f"More than one field in range query [{fields}]"
            )

    # limited currently to date ranges using strict_date_optional_time that have both a gte **and** lte.
    # If either is missing we error. We let other range types pass through unaffected
    def process(self, date_data):
        if self.upper_bound and self.lower_bound:
            new_lower, new_upper = date_data.generate_new_bounds(
                self.lower_bound, self.upper_bound
            )
            self.query_range[
                "gte" if self.lower_inclusive else "gt"
            ] = f"{new_lower.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]}Z"
            self.query_range[
                "lte" if self.upper_inclusive else "lt"
            ] = f"{new_upper.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]}Z"

    def get_time_interval(self):
        if self.upper_bound and self.lower_bound:
            return self.upper_bound - self.lower_bound
        return None

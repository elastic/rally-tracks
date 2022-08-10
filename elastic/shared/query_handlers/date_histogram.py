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
from esrally import exceptions


class DateHistogramHandler:
    def __init__(self, request_body):
        self.request_body = request_body
        self.extended_bounds = None
        self.max_bound = None
        self.min_bound = None
        self.read_ranges()

    def read_ranges(self):
        if "extended_bounds" in self.request_body:
            self.extended_bounds = self.request_body["extended_bounds"]
            self.request_body["time_zone"] = "UTC"
            if "min" in self.extended_bounds and "max" in self.extended_bounds:
                try:
                    self.max_bound = datetime.datetime.utcfromtimestamp(
                        int(self.extended_bounds["max"]) / 1000
                    )
                    self.min_bound = datetime.datetime.utcfromtimestamp(
                        int(self.extended_bounds["min"]) / 1000
                    )
                except ValueError:
                    raise exceptions.TrackConfigError(
                        f"Date Histogram aggregation requires epoch milliseconds for its "
                        f'"min" and "max" extended bounds - [{self.request_body}]'
                    )
                if self.min_bound >= self.max_bound:
                    raise exceptions.TrackConfigError(
                        f'"min" extended bounds of Date Histogram aggregation cannot be greater than "max" '
                        f"- [{self.request_body}]"
                    )
            else:
                raise exceptions.TrackConfigError(
                    f'Date Histogram aggregation does not have both "min" and "max" '
                    f"for its extended bounds- [{self.request_body}]"
                )

    # limited currently to epoch times in extended bounds
    def process(self, date_data):
        if self.max_bound and self.min_bound:
            new_min, new_max = date_data.generate_new_bounds(
                self.min_bound, self.max_bound
            )
            self.extended_bounds["max"] = int(new_max.timestamp() * 1000)
            self.extended_bounds["min"] = int(new_min.timestamp() * 1000)
        # interval customizations are provided on best-effort basis; only if generate_new_bounds was invoked previously
        if "calendar_interval" in self.request_body and date_data.calendar_interval:
            self.request_body["calendar_interval"] = date_data.calendar_interval
        if "fixed_interval" in self.request_body and date_data.fixed_interval:
            self.request_body["fixed_interval"] = date_data.fixed_interval

    def get_time_interval(self):
        if self.max_bound and self.min_bound:
            return self.max_bound - self.min_bound
        return None

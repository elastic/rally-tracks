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

import logging
from shared.utils.track import mandatory


class TimestampThrottler:
    """
    This scheduler supports throttling of indexing according to the timestamp on the data. This can be used to ensure
    the data is indexed at the same rate that the timestamp changes, thus potentially allowing ingest rates to be
    throttled.

    This works by calculating an error representing the relative time we are ahead or behind the data.
    This is based on the difference between the timespan the data has covered (tracked from the first event to the
    most recent) and the time that has passed since the first time before_request was called.

    Our target is effectively error = 0. If we achieve error == 0 then we know we are tracking the data's datetime
    profile i.e. we are indexing the data the rate determined by the time between the `@timestamp` fields on the
    documents. We refer to this as the "data datetime profile" of the data.
    Our data datetime profile + noise may mean this error increases and decreases, but the objective remains the same -
    move towards minimising it and then adapt should it increase or decrease appropriately.
    We in effect react to changes in the data datetime profile.

    If this error is decreasing in absolute terms then we know we have reasonable settings and make no change.
    This ensures we don't overshoot our target (i.e. error = 0) and overcompensate - possible as we are making
    changes which have delayed reaction. We do this by calculating a simple derivative between the current error and
    previous error and making no changes if it its < 0.

    If need to make changes i.e. our derivative of error > 0, then we have 2 options:

        1. If our error > 0, we need to speed up i.e. we are behind the data datetime profile.

            If batch_size < max_bulk_size then
                bulk_size = bulk_size + increment
            else
                rate = rate - increment if rate - increment > 0 else 0

            In effect, we prefer to always increase the batch size to speed up. Once we hit a max batch size we reduce
            our rate to eventually 0 (un-throttled). This has the effect of ensuring we maximise the batch size like
            the Elastic Agent.

        2. If our error < 0, we need to throttle i.e. we are ahead of the data datetime profile.

            If rate < max_delay then
              rate = rate + increment
            else
              bulk_size = bulk_size - increment if bulk_size - increment > 1 else 1

            This reverses the speed up effect, again trying to keep the bulk size as large as possible by decreasing the
            rate. Eventually, we can't delay anymore (default max_delay is 1s) and we start to scale back our bulk size.
            We can't go slower than 1 doc every second.

    In both cases, we calculate a divisor to adjust the bulk size or rate by an increment. We calculate an increment
    by dividing the max of the target variable (e.g. max_bulk_size) by the divisor+1, and add or subtract this onto the
    current value depending on whether we need to increase or decrease it.

    The value of the divisor is equal to:

        divisor=alpha*divisor + (beta * weight * abs(last_state - state)

    Our alpha and beta values here must add up to 1 and represent constants - alpha=0.9 and beta=0.1 for now. Weight is
    equal to 0.1 * max_bulk_size or 100 by default as max_bulk_size=1000. The state simply indicates if we are
    throttling or speeding up - assume 1 and -1 respectively. Note: This appears a little different in the code as we
    combine the weight with the state for simplicity.

    This function effectively provides a sliding window that dampens according to the previous values and and whether
    there has been a state change i.e. we've changed on our rate.

    Alpha controls how we degrade our divisor when the state is stable - a larger value means we use gradual changes in
    our parameters and consider more historical values of the divisor. Smaller values mean more changes in the divisor
    and potentially allows us to be more responsive to change by effectively considering a smaller history.
    Additionally, large alpha values mean we are also more stable as we approach our target converge on equilibrium.

    Beta and the weight is only relevant when our state changes i.e. we change sign, and aims to dampen the changes we
    make when we oscillate around the target. Beta and the weight also determines the smallest increment we can make.
    A higher weight means more dampening when we do oscillate - ideally we want this as high as possible whilst still
    being responsive to change.
    """

    ALPHA = 0.90
    BETA = 1 - ALPHA
    WEIGHT_RATIO = 0.1

    def __init__(self, task):
        self.logger = logging.getLogger(__name__)
        self.max_delay = task.params.get("max-delay-secs", 1)
        self.max_bulk_size = mandatory(
            task.operation.params, "bulk-size", task.operation.type
        )
        self.weight = self.max_bulk_size * self.WEIGHT_RATIO
        self.rate = 0
        self.parameter_source = None
        self.divisor = 0
        self.last_state = 0
        self.last_error = 0
        self.first_request = True
        self.start_time = 0

    def throttle(self, weight):
        self.logger.debug("Throttling...")
        self.logger.debug(
            "Current Divisor: [%s] Last State: [%s] New State: [%s]",
            self.divisor,
            self.last_state,
            -self.weight,
        )
        self.divisor = (self.ALPHA * self.divisor) + (
            self.BETA * abs(self.last_state + self.weight)
        )
        self.logger.debug("Divisor is [%s]", self.divisor)
        if self.rate < self.max_delay:
            rate_increment = self.max_delay / (1 + self.divisor)
            new_rate = round(self.rate + rate_increment, 6)
            # increase weight first
            new_rate = new_rate if new_rate < self.max_delay else self.max_delay
            self.logger.debug("Adjusting rate from [%s]s to [%s]s", self.rate, new_rate)
            self.rate = new_rate
        else:
            # can't slow down using the rate anymore, so we start to decrease the batch size
            bulk_size_increment = self.max_bulk_size / (1 + self.divisor)
            new_bulk_size = weight - bulk_size_increment
            new_bulk_size = int(new_bulk_size if new_bulk_size > 1 else 1)
            self.logger.debug(
                "Adjusting bulk size from [%s] to [%s]", weight, new_bulk_size
            )
            self.parameter_source.set_bulk_size(new_bulk_size)
        self.last_state = self.weight * -1

    def speedup(self, weight):
        self.logger.debug("Speeding up...")
        self.logger.debug(
            "Current Divisor: [%s] Last State: [%s] New State: [%s]",
            self.divisor,
            self.last_state,
            self.weight,
        )
        self.divisor = (self.ALPHA * self.divisor) + (
            self.BETA * abs(self.last_state - self.weight)
        )
        self.logger.debug("Divisor is [%s]", self.divisor)
        if weight < self.max_bulk_size:
            # increase the bulk to the max first
            bulk_size_increment = self.max_bulk_size / (1 + self.divisor)
            new_bulk_size = weight + bulk_size_increment
            new_bulk_size = int(
                new_bulk_size
                if new_bulk_size < self.max_bulk_size
                else self.max_bulk_size
            )
            self.logger.debug(
                "Adjusting bulk size from [%s] to [%s]", weight, new_bulk_size
            )
            self.parameter_source.set_bulk_size(new_bulk_size)
        else:
            # can't use the bulk size to speed up any more so we use the rate
            rate_increment = self.max_delay / (1 + self.divisor)
            new_rate = round(self.rate - rate_increment, 6)
            new_rate = new_rate if new_rate > 0 else 0
            self.logger.debug("Adjusting rate from [%s]s to [%s]s", self.rate, new_rate)
            self.rate = new_rate
        self.last_state = self.weight

    def after_request(self, now, weight, unit, request_meta_data):
        since_start = now - self.start_time
        error = since_start - self.parameter_source.event_time_span
        self.logger.debug(
            "Error is [%s]s, Last Error was [%s]s", error, self.last_error
        )
        new_bulk_size = weight
        change_in_error = abs(error) - abs(self.last_error)
        self.logger.debug("Change in error is [%s]", change_in_error)
        if change_in_error < 0:
            # here our the absolute error is improving so we dont need to make changes i.e. we're heading in the right
            # direction! this prevents over oscillation as the effect of the changes we make are slightly delayed
            self.logger.debug("Not adjusting as absolute error has been reduced")
        elif error > 0:
            self.speedup(weight)
        else:
            self.throttle(weight)
        self.last_error = error
        self.logger.debug("Rate set to [%s]s", self.rate)
        self.logger.debug("Bulk size set to [%s]", new_bulk_size)

    def before_request(self, now):
        if self.first_request:
            self.start_time = now
            self.first_request = False

    def next(self, current):
        if self.rate > 0:
            next_time = current + self.rate
            self.logger.debug("Scheduling next event for [%s]", next_time)
            return next_time
        # un-throttled
        return 0

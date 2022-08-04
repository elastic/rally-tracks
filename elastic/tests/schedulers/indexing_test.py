import unittest

import pytest
from esrally import track
from esrally.exceptions import DataError
from shared.schedulers.indexing import TimestampThrottler

assertions = unittest.TestCase("__init__")


def test_timestamp_throttling():
    class MockParameterSource:
        bulk_size = 1000

        def set_bulk_size(self, bulk_size):
            self.bulk_size = bulk_size

    max_delay = 1
    max_bulk_size = 1000
    parameter_source = MockParameterSource()
    timestamp_throttler = TimestampThrottler(
        track.Task(
            name="test-task",
            operation=track.Operation(
                name="bulk-index",
                operation_type=track.OperationType.Bulk.name,
                params={"bulk-size": max_bulk_size},
            ),
            params={"max-delay": max_delay},
        )
    )
    timestamp_throttler.parameter_source = parameter_source
    parameter_source.event_time_span = 1
    current_time = 0

    # step 1 - we throttle with time as we're ahead - took 0.1 but data covered 1.0
    current_time = timestamp_throttler.next(current_time)
    assert current_time == 0
    timestamp_throttler.before_request(current_time)
    # some processing time - we should take a 1 sec but initially un-throttled
    current_time += 0.1
    timestamp_throttler.after_request(
        now=current_time,
        weight=parameter_source.bulk_size,
        unit="docs",
        request_meta_data={},
    )
    assert parameter_source.bulk_size == 1000
    assert timestamp_throttler.rate == 0.090909

    # step 2 - our previous change made an improvement and the error is improving
    # we expect no changes in parameters
    current_time = timestamp_throttler.next(current_time)
    assert current_time == 0.190909
    timestamp_throttler.before_request(current_time)
    # some processing time - this request takes a long time, but the previous changes have improved our convergence
    parameter_source.event_time_span += 0.3
    current_time += 0.5
    timestamp_throttler.after_request(
        now=current_time,
        weight=parameter_source.bulk_size,
        unit="docs",
        request_meta_data={},
    )
    assert parameter_source.bulk_size == 1000
    assert timestamp_throttler.rate == 0.090909

    # step 3 - iterate until we get to 1 doc per second with a batch size of 1 - we can't go  any slower
    stable = False
    previous_bulk_size = parameter_source.bulk_size
    previous_rate = timestamp_throttler.rate
    while not stable:
        current_time = timestamp_throttler.next(current_time)
        timestamp_throttler.before_request(current_time)
        current_time += 0.1
        parameter_source.event_time_span += 1.1
        timestamp_throttler.after_request(
            now=current_time,
            weight=parameter_source.bulk_size,
            unit="docs",
            request_meta_data={},
        )
        if timestamp_throttler.rate < max_delay:
            # rate should be increasing but bulk size stable
            assert timestamp_throttler.rate > previous_rate
            assert parameter_source.bulk_size == previous_bulk_size
        elif parameter_source.bulk_size != 1:
            assert timestamp_throttler.rate == max_delay
            assert parameter_source.bulk_size <= previous_bulk_size
        else:
            stable = True
        previous_bulk_size = parameter_source.bulk_size
        previous_rate = timestamp_throttler.rate

    assert timestamp_throttler.rate == max_delay
    assert parameter_source.bulk_size == 1.0
    current_time = timestamp_throttler.next(current_time)
    assertions.assertAlmostEqual(current_time, 12.10402199)
    # simulate catching up
    timestamp_throttler.before_request(current_time)
    parameter_source.event_time_span = current_time
    timestamp_throttler.after_request(
        now=current_time,
        weight=parameter_source.bulk_size,
        unit="docs",
        request_meta_data={},
    )

    # step 4 - now we speed things up, the batch size will be increased first
    timestamp_throttler.before_request(current_time)
    current_time += 1.0
    # small time span than time taken so need to speed up
    parameter_source.event_time_span += 0.5
    timestamp_throttler.after_request(
        now=current_time,
        weight=parameter_source.bulk_size,
        unit="docs",
        request_meta_data={},
    )
    assert parameter_source.bulk_size == 43
    assertions.assertAlmostEqual(timestamp_throttler.rate, 1.0)

    # step 5 - we previous change made improvement, we expect no changes
    current_time = timestamp_throttler.next(current_time)
    assertions.assertAlmostEqual(current_time, 14.10402199)
    assertions.assertAlmostEqual(parameter_source.event_time_span, 12.60402199)
    timestamp_throttler.before_request(current_time)
    current_time += 0.3
    parameter_source.event_time_span += 2.0
    timestamp_throttler.after_request(
        now=current_time,
        weight=parameter_source.bulk_size,
        unit="docs",
        request_meta_data={},
    )
    assert parameter_source.bulk_size == 43
    assertions.assertAlmostEqual(timestamp_throttler.rate, 1.0)

    # step 6 - we need to speed up and iterate until rate is 0 and batch size is 1000
    stable = False
    previous_bulk_size = parameter_source.bulk_size
    previous_rate = timestamp_throttler.rate
    while not stable:
        current_time = timestamp_throttler.next(current_time)
        timestamp_throttler.before_request(current_time)
        current_time += 1.0
        parameter_source.event_time_span += 0.1
        timestamp_throttler.after_request(
            now=current_time,
            weight=parameter_source.bulk_size,
            unit="docs",
            request_meta_data={},
        )
        if parameter_source.bulk_size < max_bulk_size:
            # rate should be increasing but bulk size stable
            assert timestamp_throttler.rate == 1.0
            assert parameter_source.bulk_size > previous_bulk_size
        elif timestamp_throttler.rate > 0:
            assert timestamp_throttler.rate <= previous_rate
            assert parameter_source.bulk_size == max_bulk_size
        else:
            stable = True
        previous_bulk_size = parameter_source.bulk_size
        previous_rate = timestamp_throttler.rate


def test_no_bulk_size():
    with pytest.raises(DataError):
        TimestampThrottler(
            track.Task(
                name="test-task",
                operation=track.Operation(
                    name="bulk-index",
                    operation_type=track.OperationType.Bulk.name,
                    params={},
                ),
                params={"max-delay": 1},
            )
        )

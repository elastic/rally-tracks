from esrally.exceptions import TrackConfigError

from shared.utils.time import DateTimeValues
from shared.query_handlers import DateHistogramHandler
import datetime
import pytest

start = datetime.datetime(
    year=2020,
    month=12,
    day=2,
    hour=12,
    minute=33,
    second=0,
    tzinfo=datetime.timezone.utc,
)


def test_process_inclusive():
    date_histogram_agg = {
        "field": "@timestamp",
        "min_doc_count": 0,
        "time_zone": "UTC",
        "extended_bounds": {"min": 1607344057565, "max": 1607344957565},
        "fixed_interval": "10s",
    }
    date_histogram_handler = DateHistogramHandler(date_histogram_agg)
    date_histogram_handler.process(
        DateTimeValues(min_date=None, max_date=start, duration=None)
    )
    assert date_histogram_agg["extended_bounds"]["min"] == 1606911480000
    assert date_histogram_agg["extended_bounds"]["max"] == 1606912380000


def test_process_expand_bounds_with_duration():
    date_histogram_agg = {
        "field": "@timestamp",
        "min_doc_count": 0,
        "time_zone": "UTC",
        "extended_bounds": {"min": 1607344057565, "max": 1607344957565},
        "fixed_interval": "10s",
    }
    date_histogram_handler = DateHistogramHandler(date_histogram_agg)
    duration = datetime.timedelta(days=5)
    date_histogram_handler.process(
        DateTimeValues(min_date=None, max_date=start, duration=duration)
    )
    assert date_histogram_agg["extended_bounds"]["min"] == 1606480380000
    assert date_histogram_agg["extended_bounds"]["max"] == 1606912380000
    assert date_histogram_agg["fixed_interval"] == "1h"


def test_process_contract_bounds_with_duration():
    date_histogram_agg = {
        "field": "@timestamp",
        "min_doc_count": 0,
        "time_zone": "UTC",
        "extended_bounds": {"min": 1607344057565, "max": 1607344957565},
        "fixed_interval": "1m",
    }
    date_histogram_handler = DateHistogramHandler(date_histogram_agg)
    duration = datetime.timedelta(minutes=10)
    date_histogram_handler.process(
        DateTimeValues(min_date=None, max_date=start, duration=duration)
    )
    assert date_histogram_agg["extended_bounds"]["min"] == 1606911780000
    assert date_histogram_agg["extended_bounds"]["max"] == 1606912380000
    assert date_histogram_agg["fixed_interval"] == "10s"


def test_process_contract_bounds_with_min_date():
    date_histogram_agg = {
        "field": "@timestamp",
        "min_doc_count": 0,
        "time_zone": "UTC",
        "extended_bounds": {"min": 1607344057565, "max": 1607344957565},
        "fixed_interval": "1m",
    }
    date_histogram_handler = DateHistogramHandler(date_histogram_agg)
    min_date = datetime.datetime.utcfromtimestamp(1606911780).replace(
        tzinfo=datetime.timezone.utc
    )
    date_histogram_handler.process(
        DateTimeValues(min_date=min_date, max_date=start, duration=None)
    )
    assert date_histogram_agg["extended_bounds"]["min"] == 1606911780000
    assert date_histogram_agg["extended_bounds"]["max"] == 1606912380000
    assert date_histogram_agg["fixed_interval"] == "10s"


def test_missing_min():
    with pytest.raises(TrackConfigError) as rae:
        DateHistogramHandler(
            {
                "field": "@timestamp",
                "min_doc_count": 0,
                "time_zone": "UTC",
                "extended_bounds": {"max": 1607344957565},
                "fixed_interval": "10s",
            }
        ).process(DateTimeValues(min_date=None, max_date=start, duration=None))
    assert (
        rae.value.message
        == 'Date Histogram aggregation does not have both "min" and "max" for its extended '
        "bounds- [{'field': '@timestamp', 'min_doc_count': 0, 'time_zone': 'UTC', "
        "'extended_bounds': {'max': 1607344957565}, 'fixed_interval': '10s'}]"
    )


def test_missing_max():
    with pytest.raises(TrackConfigError) as rae:
        DateHistogramHandler(
            {
                "field": "@timestamp",
                "min_doc_count": 0,
                "time_zone": "UTC",
                "extended_bounds": {"min": 1607344057565},
                "fixed_interval": "10s",
            }
        ).process(DateTimeValues(min_date=None, max_date=start, duration=None))
    assert (
        rae.value.message
        == 'Date Histogram aggregation does not have both "min" and "max" for its extended '
        "bounds- [{'field': '@timestamp', 'min_doc_count': 0, 'time_zone': 'UTC', "
        "'extended_bounds': {'min': 1607344057565}, 'fixed_interval': '10s'}]"
    )


# currently we only support epoch dates
def test_missing_invalid_bounds():
    with pytest.raises(TrackConfigError) as rae:
        DateHistogramHandler(
            {
                "field": "@timestamp",
                "min_doc_count": 0,
                "time_zone": "UTC",
                "extended_bounds": {
                    "min": "2020-11-30T12:16:59.340Z",
                    "max": "2020-12-01T12:16:59.340Z",
                },
                "fixed_interval": "10s",
            }
        ).process(DateTimeValues(min_date=None, max_date=start, duration=None))
    assert (
        rae.value.args[0]
        == 'Date Histogram aggregation requires epoch milliseconds for its "min" and "max" '
        "extended bounds - [{'field': '@timestamp', 'min_doc_count': 0, 'time_zone': 'UTC', "
        "'extended_bounds': {'min': '2020-11-30T12:16:59.340Z', 'max': "
        "'2020-12-01T12:16:59.340Z'}, 'fixed_interval': '10s'}]"
    )


def test_invalid_configured_min_max():
    with pytest.raises(TrackConfigError) as err:
        # fall back on max but configured query_min_date is after original extended_bounds.max
        zealous_min = datetime.datetime(year=2021, month=1, day=1).replace(
            tzinfo=datetime.timezone.utc
        )
        DateHistogramHandler(
            {
                "field": "@timestamp",
                "min_doc_count": 0,
                "time_zone": "UTC",
                "extended_bounds": {"max": 1607344957565, "min": 1607344057565},
                "fixed_interval": "10s",
            }
        ).process(DateTimeValues(min_date=zealous_min, max_date=start, duration=None))
    assert err.value.message == (
        "query-min-date 2021-01-01 00:00:00+00:00 cannot be larger than effective "
        "query-max-date 2020-12-02 12:33:00+00:00"
    )


def test_missing_invalid_range_bounds():
    with pytest.raises(TrackConfigError) as rae:
        DateHistogramHandler(
            {
                "field": "@timestamp",
                "min_doc_count": 0,
                "time_zone": "UTC",
                "extended_bounds": {"max": 1607344057565, "min": 1607344957565},
                "fixed_interval": "10s",
            }
        ).process(DateTimeValues(min_date=None, max_date=start, duration=None))
    assert (
        rae.value.message
        == '"min" extended bounds of Date Histogram aggregation cannot be greater than "max"'
        " - [{'field': '@timestamp', 'min_doc_count': 0, 'time_zone': 'UTC', "
        "'extended_bounds': {'max': 1607344057565, 'min': 1607344957565}, 'fixed_interval': "
        "'10s'}]"
    )


# test pass through if no extended bounds
def test_pass_through_if_no_bounds():
    date_histogram_agg = {
        "field": "@timestamp",
        "min_doc_count": 0,
        "time_zone": "UTC",
        "fixed_interval": "10s",
    }
    date_histogram_handler = DateHistogramHandler(date_histogram_agg)
    date_histogram_handler.process(
        DateTimeValues(min_date=None, max_date=start, duration=None)
    )
    assert "extended_bounds" not in date_histogram_agg


def test_get_time_interval():
    date_histogram_agg = {
        "field": "@timestamp",
        "min_doc_count": 0,
        "time_zone": "UTC",
        "extended_bounds": {"min": 1607344057565, "max": 1607344957565},
        "fixed_interval": "10s",
    }
    date_histogram_handler = DateHistogramHandler(date_histogram_agg)
    time_interval = date_histogram_handler.get_time_interval()
    assert time_interval.total_seconds() == 900


def test_get_time_interval_is_idempotent():
    date_histogram_agg = {
        "field": "@timestamp",
        "min_doc_count": 0,
        "time_zone": "UTC",
        "extended_bounds": {"min": 1607344057565, "max": 1607344957565},
        "fixed_interval": "10s",
    }
    date_histogram_handler = DateHistogramHandler(date_histogram_agg)
    time_interval = date_histogram_handler.get_time_interval()
    date_histogram_handler.process(
        DateTimeValues(min_date=None, max_date=start, duration=None)
    )
    assert time_interval == date_histogram_handler.get_time_interval()

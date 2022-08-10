import os
from datetime import datetime, timezone

DEFAULT_START_DATE = "now-1d"
DEFAULT_END_DATE = "now"
DEFAULT_MAX_DATE = "2020-01-01"

# this provides a universal start date for `now` if we are using it as the current time
now = datetime.utcnow().replace(tzinfo=timezone.utc)


def utc_now():
    return now


def add_track_path(track, params, **kwargs):
    """
    transparently appends track path to provided params in operation
    """
    params["track-path"] = track.root
    return params

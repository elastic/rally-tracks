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


def add_asset_paths(track, params, **kwargs):
    """
    transparently appends the asset paths to provided params in operation
    """
    params["asset-paths"] = [
        os.path.join(assets_group["path"], package)
        for assets_group in track.selected_challenge_or_default.parameters.get("assets", [])
        for package in assets_group["packages"]
    ]
    return params

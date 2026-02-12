# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import datetime as dt
from dataclasses import dataclass, field
from typing import Any


# ------------------- Date helpers -----------------
def convert_str_to_date(date_str: str) -> dt.datetime:
    """Convert dates in ISO 8601 to datetime object."""
    try:
        return dt.datetime.strptime(date_str, ISO_FORMAT).replace(tzinfo=dt.timezone.utc)
    except ValueError as e:
        raise RuntimeError(f"Invalid date format: {date_str}") from e


def lookback_cutoff(now, lookback: int) -> dt.datetime:
    """Return the cutoff datetime for a given lookback period in days."""
    return now - dt.timedelta(days=lookback)


# ---------------- GitHub Helper Definitions -----------------
@dataclass
class Label:
    """Represents a single label."""

    name: str = field(default_factory=str)
    color: str = field(default="ffffff")

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Label):
            return NotImplemented
        return self.name == other.name

    def get(self, key: str, default: str = "") -> str:
        return getattr(self, key, default)


@dataclass
class Comment:
    """Represents a single issue comment.

    Fields:
      body: The text content of the comment.
      created_at: ISO 8601 timestamp string representing when the comment was created.
    """

    body: str
    created_at: str
    is_reminder: bool = False

    def created_at_dt(self) -> dt.datetime:
        """Return the `created_at` value parsed as a timezone-aware UTC datetime.
        Raises:
            RuntimeError: If `created_at` is missing or not in the expected ISO 8601 format.
        """
        if not self.created_at:
            raise RuntimeError("Missing created_at field")
        try:
            return dt.datetime.strptime(self.created_at, ISO_FORMAT).replace(tzinfo=dt.timezone.utc)
        except ValueError as e:
            raise RuntimeError(f"Invalid created_at format: {self.created_at}") from e

    def get(self, key: str, default: str = "") -> str:
        return getattr(self, key, default)


@dataclass
class GHRoute:
    """Single GitHub route definition for a scenario.

    Fields:
        path: Fully expanded path expected (query params included if any).
        method: HTTP method (default GET).
        response: JSON (dict or list) returned by mock.
        status: HTTP status (>=400 triggers RuntimeError in mock invocation)
        exception: If set, raised instead of using status/response.
    """

    path: str
    method: str = "GET"
    response: dict[str, Any] | list[dict[str, Any]] = field(default_factory=dict)
    status: int = 200
    exception: BaseException | None = None


# ------------------- Constants -----------------

TEST_REPO = "test/repo"

SEARCH_LABELS_PER_PAGE = 100
SEARCH_ISSUES_PER_PAGE = 100

# We define a NOW constant for consistent use in tests.
NOW = "2025-10-30T12:00:00Z"
ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# Note that we should not import from the backport module directly to avoid circular imports.
PENDING_LABEL = "backport pending"
PENDING_LABEL_COLOR = "fff2bf"

LABELS = {
    "pending": [Label(PENDING_LABEL)],
    "pending_typo": [Label(name) for name in ["backport pend", "Backport Pending", "BACKPORT PENDING"]],
    "pending_duplicate": [Label(name) for name in [PENDING_LABEL, PENDING_LABEL]],
    "backport": [Label(name) for name in ["backport"]],
    "backport_typo": [Label(name) for name in ["backprt", "back-port", "Backport"]],
    "versioned": [Label(name) for name in ["v9.2"]],
    "versioned_typo": [Label(name) for name in ["v9.2124215s", "123.v2.1sada", "version9.2", "..v9.2..", "v!@#9.20%^@"]],
    "versioned_pending": [Label(name) for name in ["v9.2", PENDING_LABEL]],  # for remove tests
    "versioned_pending_typo": [Label(name) for name in ["v9.2", "backport pend"]],
}

COMMENT_MARKER_BASE = "<!-- backport-pending-reminder -->"
COMMENTS = {
    "recent_reminder": Comment(f"{COMMENT_MARKER_BASE}\nThis is a recent reminder.", created_at="2025-10-23T12:00:00Z", is_reminder=True),
    "reminder_slightly_older_than_a_week": Comment(
        f"{COMMENT_MARKER_BASE}\nThis is a recent reminder, just above the 7 days threshold.",
        created_at="2025-10-23T10:00:00Z",
        is_reminder=True,
    ),
    "old_reminder": Comment(f"{COMMENT_MARKER_BASE}\nThis is an old reminder.", created_at="2025-10-01T12:00:00Z", is_reminder=True),
    "really_old_reminder": Comment(
        f"\nThis is a really old reminder.{COMMENT_MARKER_BASE}", created_at="2023-10-01T12:00:00Z", is_reminder=True
    ),
    "old_comment": Comment("This is just a regular old comment without any markers.", created_at="2025-10-01T12:00:00Z", is_reminder=False),
    "strange_new_comment": Comment(
        "@!#%@!@# This is a strange comment without any markers. $$$%^&*()", created_at="2025-10-23T12:00:00Z", is_reminder=False
    ),
    "recent_comment": Comment(
        "This is just a regular recent comment without any markers.", created_at="2025-10-23T12:00:00Z", is_reminder=False
    ),
    "marker_only_new_comment": Comment(COMMENT_MARKER_BASE, created_at="2025-10-23T12:00:00Z", is_reminder=False),
    "marker_in_text_of_new_comment": Comment(
        f"Please note: {COMMENT_MARKER_BASE} this is important.", created_at="2025-10-23T12:00:00Z", is_reminder=False
    ),
    "marker_in_old_comment_difficult": Comment(
        f"sadcas@!#!@<<<<{COMMENT_MARKER_BASE}>>>>sadcas12!$@%!", created_at="2025-10-10T12:00:00Z", is_reminder=False
    ),
    "120_old_comments": [Comment(f"Comment number {i}", created_at="2025-10-01T12:00:00Z", is_reminder=False) for i in range(120)],
}
COMMENTS_PER_PAGE = 100


STATIC_ROUTES = {
    "create_pending_label": GHRoute(
        path=f"/repos/{TEST_REPO}/labels", method="POST", response={"name": PENDING_LABEL, "color": PENDING_LABEL_COLOR}
    ),
    "get_labels": GHRoute(path=f"/repos/{TEST_REPO}/labels?per_page={SEARCH_LABELS_PER_PAGE}", method="GET", response=[]),
    "search_issues": GHRoute(path=f"/search/issues...merged...updated...", method="GET", response={}),
}

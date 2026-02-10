"""Minimal registry of pull request test cases.

This module intentionally keeps ONLY:
    - A single list `PR_CASES` containing all `PullRequestCase` objects.
    - A helper `select_pull_requests(**filters)` that filters by attributes that
        exist directly on `PullRequestCase` (e.g. number, merged, needs_pending, needs_reminder, labels, etc.).

No classification metadata, wrapper dataclasses, or pattern axes are retained.
If higher-level categorization is needed, compose it at call sites.
"""

from __future__ import annotations

from dataclasses import asdict
from enum import Enum
from typing import Any

from github_ci_tools.tests.resources.cases import PullRequestCase
from github_ci_tools.tests.utils import (
    COMMENTS,
    COMMENTS_PER_PAGE,
    LABELS,
    NOW,
    SEARCH_LABELS_PER_PAGE,
    TEST_REPO,
    GHRoute,
    convert_str_to_date,
    lookback_cutoff,
)


def _pr(**kwargs) -> PullRequestCase:
    """Thin helper to create PullRequestCase with minimal kwargs."""
    return PullRequestCase(**kwargs)


# ----------------------- Static PR Cases -----------------------
PR_CASES: list[PullRequestCase] = [
    _pr(number=101, merged_at="2025-10-23T12:00:00Z", needs_pending=True),
    _pr(
        number=102,
        merged_at="2025-10-23T12:00:00Z",
        needs_pending=True,
        comments=[
            COMMENTS["recent_comment"],
            COMMENTS["old_reminder"],
            COMMENTS["old_comment"],
        ],
    ),
    _pr(
        number=103,
        merged_at="2025-10-23T12:00:00Z",
        labels=LABELS["versioned_typo"],
        needs_pending=True,
        comments=[
            COMMENTS["recent_reminder"],
            COMMENTS["old_comment"],
        ],
    ),
    _pr(
        number=104,
        merged_at="2025-10-02T12:00:00Z",
        labels=LABELS["versioned"],
        needs_reminder=True,
    ),
    _pr(
        number=105,
        merged_at="2025-10-02T12:00:00Z",
        labels=LABELS["backport"],
        comments=[
            COMMENTS["recent_comment"],
            COMMENTS["recent_reminder"],
        ],
    ),
    _pr(
        number=106,
        merged_at="2025-10-02T12:00:00Z",
        labels=LABELS["versioned_pending"],
        backport_pending_in_labels=True,
        needs_reminder=True,
        comments=[
            COMMENTS["recent_comment"],
        ],
    ),
    _pr(
        number=107,
        merged_at="2025-10-02T12:00:00Z",
        labels=LABELS["pending_typo"],
        needs_pending=True,
        comments=[
            COMMENTS["strange_new_comment"],
            COMMENTS["old_reminder"],
        ],
    ),
    _pr(
        number=108,
        merged_at="2025-10-02T12:00:00Z",
        labels=LABELS["versioned_pending_typo"],
        comments=[
            COMMENTS["recent_comment"],
            COMMENTS["marker_in_old_comment_difficult"],
            COMMENTS["marker_only_new_comment"],
            COMMENTS["really_old_reminder"],
        ],
    ),
    _pr(
        number=109,
        merged_at="2025-10-23T12:00:00Z",
        labels=LABELS["pending_typo"],
        needs_pending=True,
        comments=[
            COMMENTS["recent_comment"],
            COMMENTS["marker_in_old_comment_difficult"],
            COMMENTS["really_old_reminder"],
        ],
    ),
    _pr(
        number=110,
        merged_at="2025-10-23T10:00:00Z",
        labels=LABELS["pending"],
        backport_pending_in_labels=True,
        needs_reminder=True,
        comments=[
            COMMENTS["reminder_slightly_older_than_a_week"],
            COMMENTS["old_reminder"],
            COMMENTS["old_comment"],
        ],
    ),
    # Unmerged PRs should be ignored no matter what their state is.
    _pr(number=201, merged=False, needs_pending=True, needs_reminder=True),
    _pr(
        number=202,
        merged=False,
        labels=LABELS["versioned"],
        comments=[COMMENTS["marker_in_text_of_new_comment"]],
    ),
    _pr(
        number=203,
        merged=False,
        labels=LABELS["versioned_typo"],
        needs_pending=True,
        comments=[
            COMMENTS["really_old_reminder"],
        ],
    ),
    _pr(
        number=204,
        merged=False,
        labels=LABELS["versioned_pending_typo"],
        comments=[
            COMMENTS["recent_comment"],
        ],
    ),
    # Old merged PRs for lookback and reminder age testing
    _pr(number=301, merged_at="2023-10-01T12:00:00Z", needs_pending=True),
    _pr(
        number=302,
        merged_at="2023-10-01T12:00:00Z",
        needs_pending=True,
        comments=[
            COMMENTS["really_old_reminder"],
        ],
    ),
    _pr(
        number=303,
        merged_at="2023-10-01T12:00:00Z",
        needs_pending=True,
        comments=[
            COMMENTS["old_reminder"],
            COMMENTS["strange_new_comment"],
            COMMENTS["really_old_reminder"],
        ],
    ),
    _pr(
        number=304,
        merged_at="2023-10-01T12:00:00Z",
        labels=LABELS["versioned"],
    ),
    _pr(
        number=305,
        merged_at="2023-10-01T12:00:00Z",
        labels=LABELS["backport"],
        comments=[
            COMMENTS["really_old_reminder"],
        ],
    ),
    _pr(
        number=306,
        merged_at="2023-10-01T12:00:00Z",
        labels=LABELS["backport_typo"],
        needs_pending=True,
        comments=[
            COMMENTS["marker_in_text_of_new_comment"],
        ],
    ),
    _pr(
        number=307,
        merged_at="2023-10-01T12:00:00Z",
        labels=LABELS["pending"],
        backport_pending_in_labels=True,
        needs_reminder=True,
        comments=[
            COMMENTS["marker_in_old_comment_difficult"],
        ],
    ),
    _pr(
        number=308,
        merged_at="2023-10-01T12:00:00Z",
        labels=LABELS["versioned_typo"],
        needs_pending=True,
        comments=[
            COMMENTS["old_reminder"],
            COMMENTS["strange_new_comment"],
        ],
    ),
    _pr(
        number=309,
        merged_at="2023-10-01T12:00:00Z",
        needs_pending=True,
        comments=COMMENTS["120_old_comments"],
    ),
    # PRs marked for removal of pending label
    _pr(number=401, merged_at="2023-10-01T12:00:00Z", needs_pending=True, remove=True),
    _pr(
        number=402,
        merged_at="2023-10-01T12:00:00Z",
        labels=LABELS["pending"],
        backport_pending_in_labels=True,
        needs_reminder=True,
        comments=[
            COMMENTS["really_old_reminder"],
        ],
        remove=True,
    ),
    _pr(
        number=403,
        merged_at="2023-10-01T12:00:00Z",
        labels=LABELS["pending_typo"],
        needs_pending=True,
        comments=[
            COMMENTS["old_reminder"],
            COMMENTS["strange_new_comment"],
            COMMENTS["really_old_reminder"],
        ],
        remove=True,
    ),
]


# ----------------------- Selectors -----------------------
def select_pull_requests(**filters: Any) -> list[PullRequestCase]:
    """Return PullRequestCase objects matching direct attribute equality filters.

    Example: select_pull_requests(merged=True, needs_pending=True)
    Only attributes present on PullRequestCase are supported. Unknown keys raise ValueError.
    lists (e.g. labels) match by direct equality.
    """
    if not filters:
        return list(PR_CASES)
    unsupported = [k for k in filters.keys() if not hasattr(PR_CASES[0], k)] if PR_CASES else []
    if unsupported:
        raise ValueError(f"Unsupported filter keys: {unsupported}")
    out: list[PullRequestCase] = []
    for pr in PR_CASES:
        keep = True
        for k, v in filters.items():
            k_val = getattr(pr, k)
            if k_val != v:
                if isinstance(k_val, list):
                    if not any(item in v for item in k_val):
                        keep = False
                        break
                else:
                    keep = False
                    break
        if keep:
            out.append(pr)
    return out


def case_by_number(number: int) -> PullRequestCase:
    return next(pr for pr in PR_CASES if pr.number == number)


def select_pull_requests_by_lookback(lookback_days: int, **filters) -> list[PullRequestCase]:
    """Return PullRequestCase objects merged within lookback_days from NOW."""
    filtered_prs = select_pull_requests(**filters)
    now = convert_str_to_date(NOW)
    out: list[PullRequestCase] = []
    for pr in filtered_prs:
        if pr.merged and pr.merged_at:
            merged_at_date = convert_str_to_date(pr.merged_at)
            if merged_at_date >= lookback_cutoff(now, lookback_days):
                out.append(pr)
    return out


# ----------------------- Test case utilities -----------------------
class GHInteractAction(Enum):
    PR_ADD_PENDING_LABEL = "add_pending_label"
    PR_REMOVE_PENDING_LABEL = "remove_pending_label"
    PR_GET_COMMENTS = "get_comments"
    PR_POST_REMINDER_COMMENT = "post_reminder_comment"
    REPO_GET_LABELS = "get_repo_labels"
    REPO_ADD_LABEL = "add_repo_label"
    ITER_PRS = "iter_prs"


def build_gh_routes_comments(method: str, prs: list[PullRequestCase]) -> list[GHRoute]:
    routes = []
    for pr in prs:
        if method == "POST":
            routes.append(
                GHRoute(
                    f"/repos/{TEST_REPO}/issues/{pr.number}/comments",
                    method=method,
                    response={},
                )
            )
        elif method == "GET":
            comments_length = len(pr.comments)
            if comments_length == 0:
                routes.append(
                    GHRoute(
                        f"/repos/{TEST_REPO}/issues/{pr.number}/comments...",
                        method=method,
                        response=[],
                    )
                )
                continue
            num_pages = (comments_length + COMMENTS_PER_PAGE - 1) // COMMENTS_PER_PAGE

            for page in range(1, num_pages + 1):
                start_idx = (page - 1) * COMMENTS_PER_PAGE
                end_idx = min(start_idx + COMMENTS_PER_PAGE, comments_length)
                page_comments = pr.comments[start_idx:end_idx]
                routes.append(
                    GHRoute(
                        f"/repos/{TEST_REPO}/issues/{pr.number}/comments...&page={page}",
                        method=method,
                        response=[asdict(comment) for comment in page_comments],
                    )
                )
        else:
            raise ValueError(f"Unsupported method for comment routes: {method}")
    return routes


def build_gh_routes_labels(method: str, prs: list[PullRequestCase]) -> list[GHRoute]:
    routes = []
    for pr in prs:
        routes.append(
            GHRoute(
                f"/repos/{TEST_REPO}/issues/{pr.number}/labels",
                method=method,
                response=[{"name": label.name, "color": label.color} for label in pr.labels],
            )
        )
    return routes


def build_gh_routes_repo() -> list[GHRoute]:
    return [
        GHRoute(
            f"/repos/{TEST_REPO}/labels",
            method="GET",
            response={},
        ),
        GHRoute(
            f"/repos/{TEST_REPO}/labels",
            method="POST",
            response={},
        ),
    ]


def expected_actions_for_prs(action: GHInteractAction, prs: list[PullRequestCase], lookback_mode: str = "updated") -> list[tuple[str, str]]:
    actions = []
    match action:
        case GHInteractAction.PR_ADD_PENDING_LABEL:
            for pr in prs:
                actions.append(("POST", f"/repos/{TEST_REPO}/issues/{pr.number}/labels"))
        case GHInteractAction.PR_REMOVE_PENDING_LABEL:
            for pr in prs:
                actions.append(("DELETE", f"/repos/{TEST_REPO}/issues/{pr.number}/labels"))
        case GHInteractAction.PR_GET_COMMENTS:
            for pr in prs:
                num_pages = (len(pr.comments) + COMMENTS_PER_PAGE - 1) // COMMENTS_PER_PAGE
                if num_pages == 0:
                    actions.append(("GET", f"/repos/{TEST_REPO}/issues/{pr.number}/comments?per_page={COMMENTS_PER_PAGE}&page=1"))
                for page in range(1, num_pages + 1):
                    actions.append(("GET", f"/repos/{TEST_REPO}/issues/{pr.number}/comments?per_page={COMMENTS_PER_PAGE}&page={page}"))
        case GHInteractAction.PR_POST_REMINDER_COMMENT:
            for pr in prs:
                actions.append(("POST", f"/repos/{TEST_REPO}/issues/{pr.number}/comments"))
        case GHInteractAction.ITER_PRS:
            actions.append(("GET", f"/search/issues...merged...{lookback_mode}..."))
        case _:
            raise ValueError(f"Unsupported PR action: {action}")
    return actions


def expected_actions_for_repo(action: GHInteractAction) -> list[tuple[str, str]]:
    actions = []
    match action:
        case GHInteractAction.REPO_GET_LABELS:
            actions.append(("GET", f"/repos/{TEST_REPO}/labels?per_page={SEARCH_LABELS_PER_PAGE}"))
        case GHInteractAction.REPO_ADD_LABEL:
            actions.append(("POST", f"/repos/{TEST_REPO}/labels"))
        case _:
            raise ValueError(f"Unsupported repo action: {action}")
    return actions

#!/usr/bin/env python3

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

"""Backport CLI

- Apply 'backport pending' label to merged PRs that require backport.
- Post reminder comments on such PRs that have a 'backport pending' label
but a version label (e.g. v9.2) has not been added yet. 
- Omits PRs labeled 'backport'.

Usage: backport.py [options] <command> [flags]

Options:
    --repo                               owner/repo
    --pr-mode                            Single PR mode (use event payload); Handle PR through GITHUB_EVENT_PATH.
    -v, --verbose                        Increase verbosity (can be repeated: -vv)
    -q, --quiet                          Decrease verbosity (can be repeated: -qq)
    --dry-run                            Simulate actions without modifying GitHub state

Commands:
    label                               Add 'backport pending' label to merged PRs lacking version/backport labels
    remind                              Post reminders on merged PRs still pending backport

Flags:
    --lookback-days N                    Days to scan in bulk
    --pending-reminder-age-days M           Days between reminders
    --remove                             Remove 'backport pending' label

Quick usage:
    backport.py label --pr-mode
    backport.py --repo owner/name label --lookback-days 7
    backport.py --repo owner/name remind --lookback-days 30 --pending-reminder-age-days 14
    backport.py --repo owner/name --dry-run -vv label --lookback-days 30

Logic:
    Add label when: no version label (regex vX(.Y)), no pending or 'backport' label.
    Remind when: pending label present AND (no previous reminder OR last reminder older than M days).
    Marker: <!-- backport-pending-reminder -->

Exit codes: 0 success / 1 error.
"""

import argparse
import datetime as dt
import json
import logging
import os
import re
import sys
import urllib.error
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

LOG = logging.getLogger(__name__)

ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
VERSION_LABEL_RE = re.compile(r"^v\d{1,2}(?:\.\d{1,2})?$")
BACKPORT_LABEL = "backport"
PENDING_LABEL = "backport pending"
PENDING_LABEL_COLOR = "fff2bf"
COULD_NOT_CREATE_LABEL_WARNING = "Could not create label"
GITHUB_API = "https://api.github.com"
COMMENT_MARKER_BASE = "<!-- backport-pending-reminder -->"  # static for detection
REMINDER_BODY = (
    "A backport is pending for this PR. Please add all required version labels.\n\n"
    "   - If it is intended for the current release version, apply the corresponding version label (e.g. v9.2).\n"
    "   - If it also supports past released versions, add those labels too (e.g. v9.0 and v9.1).\n"
    "   - If it only targets a future version (e.g. v9.3), wait until that version label exists and then add it.\n"
    "     (Each rally-tracks version label is created during the feature freeze of the next ES branch).\n\n"
    "Backporting entails: \n"
    "   1. Ensuring the correct version labels exist in this PR\n"
    "   2. Ensuring normal execution of the automatically produced GH actions in the 'Actions' tab\n"
    "   3. Ensuring there is an open PR for each target version branch.\n"
    "   4. Ensuring backport PRs have the 'backport' label and start with the version branch they are targeting.\n"
    "   5. Merge the backport PRs.\n"
    "   6. Remove the 'backport pending' label from this PR once all backport PRs are merged.\n\n"
    "At each of the step process you can reach out the es-perf team to help you address the backporting process.\n"
    "Thank you!"
)


@dataclass
class BackportConfig:
    token: str | None = None
    repo: str | None = None
    dry_run: bool = False
    log_level: int = logging.INFO
    command: str | None = None
    verbose: int = 0
    quiet: int = 0


CONFIG = BackportConfig(
    token=os.environ.get("BACKPORT_TOKEN"),
    repo=os.environ.get("GITHUB_REPOSITORY"),
)


# ----------------------------- GH Helpers -----------------------------
def gh_request(method: str = "GET", path: str = "", body: dict[str, Any] | None = None, params: dict[str, str] | None = None) -> Any:
    if params:
        path = f"{path}?{urlencode(params)}"
    url = f"{GITHUB_API}{path}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
    token = CONFIG.token
    # In dry-run, skip mutating requests (anything not GET) and just log.
    if is_dry_run():
        LOG.debug(f"Would {method} {url} body={json.dumps(body) if body else '{}'}")
        if method.upper() != "GET":
            return {}
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    try:
        with urllib.request.urlopen(req) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            txt = resp.read().decode(charset)
            if is_dry_run():
                LOG.debug(f"Response {resp.status} {method} {url}")
                LOG.debug(f"Response body: {txt}")
            if resp.status >= 300:
                raise RuntimeError(f"HTTP {resp.status}: {txt}")
            return json.loads(txt) if txt.strip() else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        raise RuntimeError(f"HTTP {e.code} {e.reason} {err}") from e


@dataclass
class PRInfo:
    number: int
    labels: list[str]

    def __init__(self, pr: dict[str, Any]):
        self.number = int(pr.get("number") or pr.get("url", "").rstrip("/").strip().rsplit("/", 1) or -1)
        self.labels = [lbl.get("name", "") for lbl in pr.get("labels", [])]
        if self.number == -1 and not self.labels:
            raise RuntimeError("PRInfo initialization failed: missing number and labels")


# ----------------------------- PR Extraction (single or bulk) -----------------------------
def load_event() -> dict:
    """Load the GitHub event payload from GITHUB_EVENT_PATH for single PR mode.

    Returns an empty dict if the path is missing to allow callers to decide on fallback behavior.
    """
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path or not os.path.exists(path):
        LOG.warning("GITHUB_EVENT_PATH not set or file missing; nothing to do")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_pr(event: dict) -> PRInfo | None:
    """Extract PR information from the event payload (single PR mode)."""
    pr = event.get("pull_request")
    return PRInfo(pr) if pr else None


def list_prs(q_filter: str, since: dt.datetime) -> Iterable[dict[str, Any]]:
    """Query the GH API with a filter to iterate over PRs updated after a given timestamp."""
    q_date = since.strftime("%Y-%m-%d")
    q = f"{q_filter} updated:>={q_date}"
    LOG.debug(f"Fetch PRs with filter '{q}")
    page = 1
    while True:
        result = gh_request(
            path="/search/issues",
            params={"q": f"{q}", "per_page": "100", "page": str(page)},
        )
        items = result.get("items", [])
        if not items:
            break
        for it in items:
            yield it
        if len(items) < 100:
            break
        page += 1


def repo_needs_pending_label(repo_labels: list[str]) -> bool:
    return repo_labels.count(PENDING_LABEL) == 0


def ensure_backport_pending_label() -> None:
    """If the exact PENDING_LABEL string does not appear at least once, we create it."""
    repo = CONFIG.repo
    try:
        existing = gh_request(path=f"/repos/{repo}/labels", params={"per_page": "100"})
    except Exception as e:
        LOG.info(f"Could not list labels; attempting direct create: {e}")
        existing = []
    LOG.debug(f"Repo has labels: {existing};")
    names = [lbl.get("name", "") for lbl in existing]
    if not repo_needs_pending_label(names):
        return
    try:
        gh_request(method="POST", path=f"/repos/{repo}/labels", body={"name": PENDING_LABEL, "color": PENDING_LABEL_COLOR})
    except Exception as e:
        LOG.warning(f"{COULD_NOT_CREATE_LABEL_WARNING}: {e}")


def pr_needs_pending_label(info: PRInfo) -> bool:
    pr_labels = info.labels
    has_version_label = any(VERSION_LABEL_RE.match(label) for label in pr_labels)
    has_pending = any(label == PENDING_LABEL for label in pr_labels)
    has_backport = any(label == BACKPORT_LABEL for label in pr_labels)
    return not has_version_label and not has_pending and not has_backport


def add_label(pr_number: int, label: str) -> None:
    issues_labels_api = f"/repos/{CONFIG.repo}/issues/{pr_number}/labels"
    gh_request(method="POST", path=issues_labels_api, body={"labels": [label]})
    LOG.info(f"Added label '{label}' to PR #{pr_number}")


def remove_label(pr_number: int, label: str) -> None:
    issues_labels_api = f"/repos/{CONFIG.repo}/issues/{pr_number}/labels"
    gh_request(method="DELETE", path=issues_labels_api, body={"labels": [label]})
    LOG.info(f"Removed label '{label}' from PR #{pr_number}")


def run_label(prefetched_prs: list[dict[str, Any]], remove: bool) -> int:
    """Apply label logic to prefetched merged PRs (single for pull_request_target or bulk)."""
    if not prefetched_prs:
        raise RuntimeError("No PRs prefetched for labeling")
    # Ensure repository has pending label definition before any per-PR action.
    # Doing this once avoids per-PR re-listing when add_label calls ensure_backport_pending_label.
    try:
        ensure_backport_pending_label()
    except Exception as e:  # Defensive: creation failure shouldn't block individual PR labeling attempts
        LOG.warning(f"Cannot ensure that backport pending label exists in repo: {e}")
    errors = 0
    for pr in prefetched_prs:
        try:
            if not pr:
                continue
            info = PRInfo(pr)
            if remove:
                remove_label(info.number, PENDING_LABEL)
            elif pr_needs_pending_label(info):
                add_label(info.number, PENDING_LABEL)
            else:
                LOG.debug(f"PR #{info.number}: No label action needed")
        except Exception as e:
            LOG.error(f"Label error for PR #{pr.get('number','unknown')}: {e}")
            errors += 1
    return errors


# ----------------------------- Reminder Logic -----------------------------
def get_issue_comments(number: int) -> list[dict[str, Any]]:
    comments: list[dict[str, Any]] = []
    page = 1
    repo = CONFIG.repo
    while True:
        data = gh_request(path=f"/repos/{repo}/issues/{number}/comments", params={"per_page": "100", "page": str(page)})
        if not data:
            break
        comments.extend(data)
        # We are using a page size of 100. If we get less, we are done.
        if len(data) < 100:
            break
        page += 1
    return comments


def post_comment(number: int, body: str) -> None:
    if is_dry_run():
        LOG.info(f"Would post comment to PR #{number}")
    repo = CONFIG.repo
    gh_request(method="POST", path=f"/repos/{repo}/issues/{number}/comments", body={"body": body})


def last_reminder_time(comments: list[dict[str, Any]], marker: str) -> dt.datetime | None:
    def comment_ts(c: dict[str, Any]) -> dt.datetime:
        ts_raw = c.get("created_at") or c.get("updated_at")
        if not ts_raw:
            raise RuntimeError("Comment missing timestamp fields")
        return dt.datetime.strptime(ts_raw, ISO_FORMAT).replace(tzinfo=dt.timezone.utc)

    for c in sorted(comments, key=comment_ts, reverse=True):
        body = c.get("body") or ""
        if marker in body:
            return comment_ts(c)
    return None


def pr_needs_reminder(info: PRInfo, threshold: dt.datetime) -> bool:
    if pr_needs_pending_label(info):
        return False
    comments = get_issue_comments(info.number)
    prev_time = last_reminder_time(comments, COMMENT_MARKER_BASE)
    if prev_time is None:
        return True
    return prev_time < threshold


def run_remind(prefetched_prs: list[dict[str, Any]], pending_reminder_age_days: int, lookback_days: int) -> int:
    """Post reminders using prefetched merged PR list."""
    if not prefetched_prs:
        raise RuntimeError("No PRs prefetched for reminding")
    now = dt.datetime.now(dt.timezone.utc)
    threshold = now - dt.timedelta(days=pending_reminder_age_days)
    LOG.info(
        f"prefetched={len(prefetched_prs)} lookback_days={lookback_days} pending_reminder_age_days={pending_reminder_age_days} now={now.isoformat()} threshold={threshold.isoformat()}"
    )
    errors = 0
    for pr in prefetched_prs:
        try:
            if not pr:
                continue
            info = PRInfo(pr)
            if pr_needs_reminder(info, threshold):
                author = pr.get("user", {}).get("login", "PR author")
                post_comment(info.number, f"{COMMENT_MARKER_BASE}\n@{author}\n{REMINDER_BODY}")
                LOG.info(f"PR #{info.number}: initial reminder posted")
            else:
                LOG.info(f"PR #{info.number}: cooling period not elapsed)")
        except Exception as ex:
            LOG.error(f"Remind error for PR #{pr.get('number', '?')}: {ex}")
            errors += 1
            continue
    return errors


# ----------------------------- CLI -----------------------------
def is_dry_run() -> bool:
    return CONFIG.dry_run


def require_mandatory_vars() -> None:
    """Validate critical environment / CLI inputs using CONFIG."""
    if not CONFIG.token:
        raise RuntimeError("Missing BACKPORT_TOKEN from environment.")
    repo = CONFIG.repo
    if not repo or not re.match(r"^[^/]+/[^/]+$", str(repo)):
        raise RuntimeError("Missing or invalid GITHUB_REPOSITORY. Either set it or pass --repo (owner/repo)")


def configure(args: argparse.Namespace) -> None:
    """Populate CONFIG, initialize logging, and validate required inputs.

    This centralizes setup so other entry points (tests, future subcommands)
    can reuse consistent initialization semantics.
    """
    CONFIG.dry_run = args.dry_run
    CONFIG.verbose = args.verbose
    CONFIG.quiet = args.quiet
    CONFIG.log_level = (CONFIG.quiet - CONFIG.verbose) * (logging.INFO - logging.DEBUG) + logging.INFO
    CONFIG.command = args.command
    # Always refresh token/repo from environment unless explicitly overridden via CLI.
    CONFIG.token = os.environ.get("BACKPORT_TOKEN")
    CONFIG.repo = args.repo if args.repo is not None else os.environ.get("GITHUB_REPOSITORY")
    logging.basicConfig(level=CONFIG.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    require_mandatory_vars()


def prefetch_prs(pr_mode: bool, lookback_days: int) -> list[dict[str, Any]]:
    if pr_mode:
        event = load_event()
        if event:
            pr_data = event.get("pull_request")
        else:
            raise RuntimeError("Failed to load event data")
        if not pr_data:
            raise RuntimeError(f"No pull_request data in event: {event}")
        # Ensure PR is merged.
        merged_flag = pr_data.get("merged")
        merged_at = pr_data.get("merged_at")
        if not merged_flag and not merged_at:
            raise RuntimeError(f"PR #{pr_data.get('number','?')} not merged yet; skipping.")
        try:
            merged_dt = dt.datetime.strptime(merged_at, ISO_FORMAT).replace(tzinfo=dt.timezone.utc)
        except ValueError as e:
            raise RuntimeError(f"Invalid merged_at format: {merged_at}") from e
        now = dt.datetime.now(dt.timezone.utc)
        age_days = (now - merged_dt).days
        if age_days >= lookback_days + 1:
            LOG.info(
                f"PR #{pr_data.get('number','?')} merged_at {merged_at} age={age_days}d "
                f"exceeds lookback_days={lookback_days}; filtering out."
            )
            return []
        return [pr_data]
    now = dt.datetime.now(dt.timezone.utc)
    since = now - dt.timedelta(days=lookback_days)
    repo = CONFIG.repo
    # Note that we rely on is:merged to filter out unmerged PRs.
    return list(list_prs(f"repo:{repo} is:pr is:merged", since))


def parse_args() -> argparse.Namespace:
    try:
        parser = argparse.ArgumentParser(
            description="Backport utilities",
            epilog="""\nExamples:\n  backport.py label --pr-mode\n  backport.py label --lookback-days 7\n  backport.py remind --lookback-days 30 --pending-reminder-age-days 14\n  backport.py --dry-run -vv label --lookback-days 30\n\nSingle PR mode (--pr-mode) reads the pull_request payload from GITHUB_EVENT_PATH.\nBulk mode searches merged PRs updated within --lookback-days.\n""",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        parser.add_argument(
            "--repo",
            help="Target repository in owner/repo form (overrides GITHUB_REPOSITORY env)",
            required=False,
            default=None,
        )
        parser.add_argument(
            "--pr-mode",
            action="store_true",
            help="Single PR mode (use GITHUB_EVENT_PATH pull_request payload). Default: bulk scan via search API",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate actions without modifying GitHub state",
        )
        parser.add_argument(
            "-v",
            "--verbose",
            action="count",
            default=0,
            help="Increase verbosity (can be used multiple times, e.g., -vv for more verbose)",
        )
        parser.add_argument(
            "-q",
            "--quiet",
            action="count",
            default=0,
            help="Decrease verbosity (can be used multiple times)",
        )
        sub = parser.add_subparsers(dest="command", required=True)

        p_label = sub.add_parser(
            "label", help="Add backport pending label to merged PRs lacking 'backport', 'backport pending' or version label"
        )
        p_label.add_argument(
            "--lookback-days",
            type=int,
            required=False,
            default=7,
            help="Days to look back (default: 7). Ignored in --pr-mode",
        )
        p_label.add_argument(
            "--remove",
            action="store_true",
            required=False,
            default=False,
            help="Removes backport pending label",
        )

        p_remind = sub.add_parser("remind", help="Post reminders on merged PRs still pending backport")
        p_remind.add_argument(
            "--lookback-days",
            type=int,
            required=False,
            default=7,
            help="Days to look back (default: 7). Ignored in --pr-mode",
        )
        p_remind.add_argument(
            "--pending-reminder-age-days",
            type=int,
            required=False,
            default=7,
            help="Days between reminders for the same PR (default: 7). Adds initial reminder if none posted yet.",
        )

    except Exception:
        raise RuntimeError("Command parsing failed")
    return parser.parse_args()


def main():
    try:
        args = parse_args()
        configure(args)

        LOG.debug(f"Parsed arguments: {args}")
        prefetched = prefetch_prs(args.pr_mode, args.lookback_days)
        LOG.debug(f"Prefetched {len(prefetched)} PRs for command '{args.command}': {[pr.get('number') for pr in prefetched]}")
        match args.command:
            case "label":
                return run_label(prefetched, args.remove)
            case "remind":
                return run_remind(prefetched, args.pending_reminder_age_days, args.lookback_days)
            case _:
                raise NotImplementedError(f"Unknown command {args.command}")
    except KeyError as ke:
        LOG.error(f"Missing configuration key: {ke}")
        sys.exit(1)
    except NotImplementedError as nie:
        LOG.error(f"Not implemented error: {nie}")
        sys.exit(2)
    except RuntimeError as re:
        LOG.error(f"Runtime error: {re}")
        sys.exit(3)
    except Exception as e:
        LOG.error(f"Unhandled error: {e}")
        sys.exit(4)


if __name__ == "__main__":
    main()

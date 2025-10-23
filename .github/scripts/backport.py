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
    --debug                              Enable debug logging
    --dry-run                            Simulate actions without modifying GitHub state

Commands:
    label                               Add 'backport pending' label to merged PRs lacking version/backport labels
    remind                              Post reminders on merged PRs still pending backport

Flags:
    --lookback-days N                    Days to scan in bulk
    --pending-label-age-days M           Days between reminders
    --remove                             Remove 'backport pending' label

Quick usage:
    backport.py label --pr-mode
    backport.py --repo owner/name label --lookback-days 7
    backport.py --repo owner/name remind --lookback-days 30 --pending-label-age-days 14
    backport.py --repo owner/name --dry-run --debug label --lookback-days 30

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
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List
from urllib.parse import urlencode

ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
VERSION_LABEL_RE = re.compile(r"^v\d{1,2}(?:\.\d{1,2})?$")
BACKPORT_LABEL = "backport"
PENDING_LABEL_CANONICAL = "backport pending"
PENDING_LABEL_COLOR = "fff2bf"
GITHUB_API = "https://api.github.com"
COMMENT_MARKER_BASE = "<!-- backport-pending-reminder -->"  # static for detection
REMINDER_BODY = (
    "A backport is pending for this PR. Please add all required version labels (e.g. v9.2).\n\n"
    "If it supports past released versions, add each released branch label (e.g. v9.1 and v9.2).\n"
    "If it only targets a future version, wait until that version label exists.\n"
    "After completing the backport(s), manually remove the 'backport pending' label.\n"
    "We do that to ensure proper tracking of backport status.\n\n"
    "Thank you!"
)

CONFIG: Dict[str, bool | str | None] = {
    "token": os.environ.get("BACKPORT_TOKEN"),
    "repo": os.environ.get("GITHUB_REPOSITORY"),  # owner/repo
    "dry_run": False,  # set by --dry-run
    "log_level": "INFO",  # INFO by default, set to DEBUG if --debug passed
    "command": None,  # set post-parse for logging
}


# ----------------------------- Logging -----------------------------
logger = logging.getLogger("backport")


def setup_logging(level: str) -> None:
    lvl = logging.DEBUG if level.upper() == "DEBUG" else logging.INFO
    backport_formatter = logging.Formatter(
        f"[%(asctime)s] %(levelname)s [{CONFIG.get("command")}{" (dry-run)" if is_dry_run() else ""}]: %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(backport_formatter)
    logger.addHandler(handler)
    logger.setLevel(lvl)


# ----------------------------- GH Helpers -----------------------------
def gh_request(path: str, method: str = "GET", body: Dict[str, Any] | None = None, params: Dict[str, str] | None = None) -> Any:
    if params:
        path = f"{path}?{urlencode(params)}"
    url = f"{GITHUB_API}{path}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
    token = CONFIG.get("token")
    # In dry-run, skip mutating requests (anything not GET) and just log.
    if is_dry_run():
        logger.debug(f"Would {method} {url} body={json.dumps(body) if body else '{}'}")
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
                logger.debug(f"Response {resp.status} {method} {url}")
            if resp.status >= 300:
                raise RuntimeError(f"HTTP {resp.status}: {txt}")
            return json.loads(txt) if txt.strip() else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        raise RuntimeError(f"HTTP {e.code} {e.reason} {err}") from e


# ----------------------------- Labeling Logic -----------------------------
@dataclass
class PRInfo:
    number: int
    labels: List[str]

    def __init__(self, pr: Dict[str, Any]):
        raw_number = pr.get("number")
        if raw_number is None and pr.get("url"):
            try:
                raw_number = int(pr.get("url", "/").rstrip("/").split("/")[-1])
            except Exception:
                raw_number = -1
        self.number = raw_number if isinstance(raw_number, int) else int(raw_number)
        self.labels = [lbl.get("name", "") for lbl in pr.get("labels", [])]


def load_event() -> dict:
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path or not os.path.exists(path):
        logger.warning("GITHUB_EVENT_PATH not set or file missing; nothing to do")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_pr(event: dict) -> PRInfo | None:
    pr = event.get("pull_request")
    return PRInfo(pr) if pr else None


def needs_pending_label(info: PRInfo) -> bool:
    has_version_label = any(VERSION_LABEL_RE.match(l) for l in info.labels)
    has_pending = any(l.lower() == PENDING_LABEL_CANONICAL.lower() for l in info.labels)
    has_backport = any(l.lower() == BACKPORT_LABEL.lower() for l in info.labels)
    # Add label only if no version label AND pending label absent.
    return not has_version_label and not has_pending and not has_backport


def ensure_label() -> None:
    """Create Backport Pending label if missing (color only set on create)."""
    repo = CONFIG.get("repo")
    label_api = f"/repos/{repo}/labels/{PENDING_LABEL_CANONICAL.replace(' ', '%20')}"
    try:
        gh_request(label_api)
        return  # exists
    except Exception:
        pass  # proceed to attempt creation
    create_api = f"/repos/{repo}/labels"
    try:
        gh_request(create_api, method="POST", body={"name": PENDING_LABEL_CANONICAL, "color": PENDING_LABEL_COLOR})
    except Exception as e:
        logger.warning(f"Could not create label: {e}")


def add_label(pr_number: int, label: str) -> None:
    ensure_label()
    repo = CONFIG.get("repo")
    issues_labels_api = f"/repos/{repo}/issues/{pr_number}/labels"
    gh_request(issues_labels_api, method="POST", body={"labels": [label]})
    logger.info(f"Added label '{label}' to PR #{pr_number}")


def remove_label(pr_number: int, label: str) -> None:
    repo = CONFIG.get("repo")
    issues_labels_api = f"/repos/{repo}/issues/{pr_number}/labels"
    gh_request(issues_labels_api, method="DELETE", body={"labels": [label]})
    logger.info(f"Removed label '{label}' from PR #{pr_number}")


def run_label(prefetched_prs: List[Dict[str, Any]], remove: bool) -> int:
    """Apply label logic to prefetched merged PRs (single for pull_request_target or bulk)."""
    if not prefetched_prs:
        raise RuntimeError("No PRs prefetched for labeling")
    # Using return code as we want to attempt all PRs even if some fail.
    rc = 0
    for pr in prefetched_prs:
        try:
            if not pr:
                continue
            info = PRInfo(pr)
            if remove:
                remove_label(info.number, PENDING_LABEL_CANONICAL)
            elif needs_pending_label(info):
                add_label(info.number, PENDING_LABEL_CANONICAL)
            else:
                logger.debug(f"PR #{info.number}: No label action needed")
        except Exception as e:
            logger.error(f"Label error for PR #{pr.get('number','unknown')}: {e}")
            rc = 1
    return rc


# ----------------------------- Reminder Logic -----------------------------
def list_prs(filter_q: str, since: dt.datetime) -> Iterable[Dict[str, Any]]:
    if is_dry_run():
        logger.info(f"Would list PRs with filter '{filter_q}' since {since.isoformat()}")
    q_date = since.strftime("%Y-%m-%d")
    page = 1
    while True:
        result = gh_request(
            "/search/issues",
            params={"q": f"{filter_q} updated:>={q_date}", "per_page": "100", "page": str(page)},
        )
        items = result.get("items", [])
        if not items:
            break
        for it in items:
            yield it
        if len(items) < 100:
            break
        page += 1
        time.sleep(0.25)


def get_issue_comments(number: int) -> List[Dict[str, Any]]:
    comments: List[Dict[str, Any]] = []
    page = 1
    while True:
        repo = CONFIG.get("repo")
        data = gh_request(f"/repos/{repo}/issues/{number}/comments", params={"per_page": "100", "page": str(page)})
        if not data:
            break
        comments.extend(data)
        if len(data) < 100:
            break
        page += 1
    return comments


def post_comment(number: int, body: str) -> None:
    if is_dry_run():
        logger.info(f"Would post comment to PR #{number}")
    repo = CONFIG.get("repo")
    gh_request(f"/repos/{repo}/issues/{number}/comments", method="POST", body={"body": body})


def has_pending_label(labels: List[Dict[str, Any]]) -> bool:
    names_lower = {lbl.get("name", "").lower() for lbl in labels}
    return PENDING_LABEL_CANONICAL.lower() in names_lower


def last_reminder_time(comments: List[Dict[str, Any]], marker: str) -> dt.datetime | None:
    def comment_ts(c: Dict[str, Any]) -> dt.datetime:
        ts_raw = c.get("created_at") or c.get("updated_at")
        if not ts_raw:
            raise RuntimeError("Comment missing timestamp fields")
        return dt.datetime.strptime(ts_raw, ISO_FORMAT).replace(tzinfo=dt.timezone.utc)

    for c in sorted(comments, key=comment_ts, reverse=True):
        body = c.get("body") or ""
        if marker in body:
            return comment_ts(c)
    return None


def run_remind(prefetched_prs: List[Dict[str, Any]], pending_label_age_days: int, lookback_days: int) -> int:
    """Post reminders using prefetched merged PR list."""

    now = dt.datetime.now(dt.timezone.utc)
    threshold = now - dt.timedelta(days=pending_label_age_days)
    logger.info(
        f"prefetched={len(prefetched_prs)} lookback_days={lookback_days} pending_label_age_days={pending_label_age_days} now={now.isoformat()} threshold={threshold.isoformat()}"
    )
    for pr in prefetched_prs:
        try:
            if not pr:
                continue
            info = PRInfo(pr)
            if not has_pending_label([{"name": l} for l in info.labels]):
                continue
            number = info.number
            author = pr.get("user", {}).get("login", "PR author")
            comments = get_issue_comments(number)
            prev_time = last_reminder_time(comments, COMMENT_MARKER_BASE)
            if prev_time is None:
                post_comment(number, f"{COMMENT_MARKER_BASE}\n@{author}\n{REMINDER_BODY}")
                logger.info(f"PR #{number}: initial reminder posted")
            elif prev_time < threshold:
                post_comment(number, f"{COMMENT_MARKER_BASE}\n@{author}\n{REMINDER_BODY}")
                logger.info(f"PR #{number}: follow-up reminder posted (prev {prev_time.isoformat()})")
            else:
                logger.info(f"PR #{number}: cooling period not elapsed (prev {prev_time.isoformat()})")
        except Exception as ex:
            logger.error(f"Remind error for PR #{pr.get('number', '?')}: {ex}")
            continue
    return 0


# ----------------------------- CLI -----------------------------
def is_dry_run() -> bool:
    return bool(CONFIG.get("dry_run"))


def require_mandatory_vars() -> None:
    """Validate critical environment / CLI inputs using CONFIG."""
    if not CONFIG.get("token"):
        raise RuntimeError("Missing BACKPORT_TOKEN from environment.")
    repo = CONFIG.get("repo")
    if not repo or not re.match(r"^[^/]+/[^/]+$", str(repo)):
        raise RuntimeError("Missing or invalid GITHUB_REPOSITORY. Either set it or pass --repo (owner/repo)")


def configure(args: argparse.Namespace) -> None:
    """Populate CONFIG, initialize logging, and validate required inputs.

    This centralizes setup so other entry points (tests, future subcommands)
    can reuse consistent initialization semantics.
    """
    CONFIG["dry_run"] = bool(getattr(args, "dry_run", False))
    CONFIG["log_level"] = "DEBUG" if getattr(args, "debug", False) else "INFO"
    CONFIG["command"] = getattr(args, "command", None)
    if getattr(args, "repo", None):
        CONFIG["repo"] = args.repo
    setup_logging(CONFIG["log_level"])
    require_mandatory_vars()


def prefetch_prs(pr_mode: bool, lookback_days: int) -> List[Dict[str, Any]]:
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
        return [pr_data]
    now = dt.datetime.now(dt.timezone.utc)
    since = now - dt.timedelta(days=lookback_days)
    repo = CONFIG.get("repo")
    # Note that we rely on is:merged to filter out unmerged PRs.
    return list(list_prs(f"repo:{repo} is:pr is:merged", since))


def parse_args(argv: List[str]) -> argparse.Namespace:
    try:
        parser = argparse.ArgumentParser(
            description="Backport utilities",
            epilog="""\nExamples:\n  backport.py label --pr-mode\n  backport.py label --lookback-days 7\n  backport.py remind --lookback-days 30 --pending-label-age-days 14\n  backport.py --dry-run --debug label --lookback-days 30\n\nSingle PR mode (--pr-mode) reads the pull_request payload from GITHUB_EVENT_PATH.\nBulk mode searches merged PRs updated within --lookback-days.\n""",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        parser.add_argument(
            "--repo",
            help="Target repository in owner/repo form (overrides GITHUB_REPOSITORY env)",
            required=False,
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
            "--debug",
            action="store_true",
            help="Enable verbose debug logging",
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
            "--pending-label-age-days",
            type=int,
            required=False,
            default=7,
            help="Days between reminders for the same PR (default: 7). Adds initial reminder if none posted yet.",
        )

    except Exception:
        raise RuntimeError("Command parsing failed")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    try:
        args = parse_args(argv or sys.argv[1:])
        configure(args)

        lookback = getattr(args, "lookback_days", None)
        # Prefetch PRs and run command step
        prefetched = prefetch_prs(getattr(args, "pr_mode", False), lookback) if args.command in {"label", "remind"} else []
        if args.command == "label":
            return run_label(prefetched, args.remove)
        if args.command == "remind":
            return run_remind(prefetched, args.pending_label_age_days, args.lookback_days)
        raise NotImplementedError(f"Unknown command {args.command}")
    except KeyError as ke:
        logger.error(f"Missing configuration key: {ke}")
        return 1
    except NotImplementedError as nie:
        logger.error(f"Not implemented error: {nie}")
        return 1
    except RuntimeError as re:
        logger.error(f"Runtime error: {re}")
        return 1
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

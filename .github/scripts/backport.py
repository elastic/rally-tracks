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

"""Backport CLI (label + remind)

Label merged PRs lacking a version label with 'backport pending' or send reminder
comments on such PRs until a version label (e.g. v9.2) is added.

Quick usage:
	backport.py help
	backport.py --event-name pull_request_target label
	backport.py --repo owner/repo --token TOKEN --event-name schedule label --lookback-days 7
	backport.py --repo owner/repo --token TOKEN --event-name workflow_dispatch remind --lookback-days 30 --pending-label-age-days 14

Key flags:
	--token / BACKPORT_TOKEN           GitHub token
	--repo / GITHUB_REPOSITORY         owner/repo
	--event-name                       pull_request_target | schedule | workflow_dispatch
	--lookback-days N                  Days to scan (bulk modes)
	--pending-label-age-days M         Days between reminders
	--remove                           Remove pending label (label command)

Logic:
	Add label when: no version label (regex vX(.Y)) and no pending label.
	Remind when: pending label present AND (no previous reminder OR last reminder older than M days).
	Marker: <!-- backport-pending-reminder -->

Exit codes: 0 success / 1 error.
"""

import argparse
import datetime as dt
import json
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

CONFIG: Dict[str, str | None] = {
    "token": os.environ.get("BACKPORT_TOKEN"),
    "repo": os.environ.get("GITHUB_REPOSITORY"),  # owner/repo
}


def require_mandatory_vars() -> None:
    """Validate critical environment / CLI inputs using CONFIG."""
    if not CONFIG.get("token"):
        raise RuntimeError("Missing BACKPORT_TOKEN / --token")
    repo = CONFIG.get("repo")
    if not repo or not re.match(r"^[^/]+/[^/]+$", str(repo)):
        raise RuntimeError("Missing or invalid GITHUB_REPOSITORY / --repo (expected owner/repo)")


# ----------------------------- Shared HTTP Helpers -----------------------------
def gh_request(path: str, method: str = "GET", body: Dict[str, Any] | None = None, params: Dict[str, str] | None = None) -> Any:
    if params:
        path = f"{path}?{urlencode(params)}"
    url = f"{GITHUB_API}{path}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
    token = CONFIG.get("token")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    try:
        with urllib.request.urlopen(req) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            txt = resp.read().decode(charset)
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
        print("::warning::GITHUB_EVENT_PATH not set or file missing; nothing to do", file=sys.stderr)
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_pr(event: dict) -> PRInfo | None:
    pr = event.get("pull_request")
    return PRInfo(pr) if pr else None


def needs_pending_label(info: PRInfo) -> bool:
    has_version_label = any(VERSION_LABEL_RE.match(l) for l in info.labels)
    has_pending = any(l.lower() == PENDING_LABEL_CANONICAL.lower() for l in info.labels)
    # Add label only if no version label AND pending label absent.
    return not has_version_label and not has_pending


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
        print(f"::warning::Could not create label: {e}")


def add_label(pr_number: int, label: str) -> None:
    ensure_label()
    repo = CONFIG.get("repo")
    issues_labels_api = f"/repos/{repo}/issues/{pr_number}/labels"
    gh_request(issues_labels_api, method="POST", body={"labels": [label]})
    print(f"[label] Added label '{label}' to PR #{pr_number}")


def remove_label(pr_number: int, label: str) -> None:
    repo = CONFIG.get("repo")
    issues_labels_api = f"/repos/{repo}/issues/{pr_number}/labels"
    gh_request(issues_labels_api, method="DELETE", body={"labels": [label]})
    print(f"[label] Removed label '{label}' to PR #{pr_number}")


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
                print(f"[label] PR #{info.number}: No label action needed")
        except Exception as e:
            print(f"::error::[label] PR #{pr.get('number','unknown')}: {e}", file=sys.stderr)
            rc = 1
    return rc


# ----------------------------- Reminder Logic -----------------------------
COMMENT_MARKER_BASE = "<!-- backport-pending-reminder -->"  # static for detection
REMINDER_BODY = "A backport is pending for this PR.\n\n" "Please add an appropriate version label (e.g. v9.2)\n" "Thank you!"


def list_prs(filter_q: str, since: dt.datetime) -> Iterable[Dict[str, Any]]:
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
    print(
        f"[reminder] prefetched={len(prefetched_prs)} lookback_days={lookback_days} pending_label_age_days={pending_label_age_days} now={now.isoformat()} threshold={threshold.isoformat()}"
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
                print(f"[reminder] PR #{number}: initial reminder posted")
            elif prev_time < threshold:
                post_comment(number, f"{COMMENT_MARKER_BASE}\n@{author}\n{REMINDER_BODY}")
                print(f"[reminder] PR #{number}: follow-up reminder posted (prev {prev_time.isoformat()})")
            else:
                print(f"[reminder] PR #{number}: cooling period not elapsed (prev {prev_time.isoformat()})")
        except Exception as ex:
            print(f"::error:: PR #{pr.get('number', '?')}: {ex}", file=sys.stderr)
            continue
    return 0


# ----------------------------- CLI -----------------------------
def parse_args(argv: List[str]) -> argparse.Namespace:
    try:
        parser = argparse.ArgumentParser(description="Backport label & reminder utilities")
        parser.add_argument(
            "--token",
            help="GitHub token (overrides BACKPORT_TOKEN env)",
            required=False,
        )
        parser.add_argument(
            "--repo",
            help="Target repository in owner/repo form (overrides GITHUB_REPOSITORY env)",
            required=False,
        )
        parser.add_argument(
            "--event-name",
            choices=["pull_request_target", "schedule", "workflow_dispatch"],
            required=False,
            help="GitHub event name",
        )
        sub = parser.add_subparsers(dest="command", required=True)

        p_label = sub.add_parser("label", help="Add Backport Pending label to merged PRs without version label")
        p_label.add_argument(
            "--lookback-days",
            type=int,
            required=False,
            default=1,
            help="Days to look back when not pull_request_target (default: 1). Ignored for pull_request_target single PR",
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
            required=True,
            help="Days to look back for updated merged PRs",
        )
        p_remind.add_argument(
            "--pending-label-age-days",
            type=int,
            required=True,
            help="Days between reminders for the same PR",
        )

        sub.add_parser("help", help="Print extended CLI help text")
    except Exception:
        raise RuntimeError("Command parsing failed")
    return parser.parse_args(argv)


def prefetch_prs(event_name: str, lookback_days: int) -> List[Dict[str, Any]]:
    if event_name == "pull_request_target":
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
            raise RuntimeError(f"[prefetch] PR #{pr_data.get('number','?')} not merged yet; skipping.")
        return [pr_data]
    now = dt.datetime.now(dt.timezone.utc)
    since = now - dt.timedelta(days=lookback_days)
    repo = CONFIG.get("repo")
    # Note that we rely on is:merged to filter out unmerged PRs.
    return list(list_prs(f"repo:{repo} is:pr is:merged", since))


def main(argv: List[str] | None = None) -> int:
    try:
        # Parse Args step
        args = parse_args(argv or sys.argv[1:])
        if args.command == "help":
            print((__doc__ or "").strip())
            return 0
        if getattr(args, "token", None):
            CONFIG["token"] = args.token
        if getattr(args, "repo", None):
            CONFIG["repo"] = args.repo
        lookback = getattr(args, "lookback_days", None)
        # Event name required only for operational commands.
        if args.command in {"label", "remind"} and not getattr(args, "event_name", None):
            raise RuntimeError("--event-name is required for label/remind")
        if args.command in {"label", "remind"}:
            require_mandatory_vars()

        # Prefetch PRs and run command step
        prefetched = prefetch_prs(args.event_name, lookback) if args.command in {"label", "remind"} else []
        if args.command == "label":
            return run_label(prefetched, args.remove)
        if args.command == "remind":
            return run_remind(prefetched, args.pending_label_age_days, args.lookback_days)
        raise NotImplementedError(f"Unknown command {args.command}")
    except NotImplementedError as nie:
        print(f"::error::Not implemented error: {nie}", file=sys.stderr)
    except RuntimeError as re:
        print(f"::error::Runtime error: {re}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"::error::Unhandled error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

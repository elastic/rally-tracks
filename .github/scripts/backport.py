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
	backport.py --callback pull_request_target label
	backport.py --repo owner/repo --callback schedule label --lookback-days 7
	backport.py --repo owner/repo --callback workflow_dispatch remind --lookback-days 30 --pending-label-age-days 14
    backport.py --dry-run --repo owner/repo --callback schedule label
    backport.py --dry-run --repo owner/repo --callback workflow_dispatch remind --lookback-days 30 --pending-label-age-days 14

Flags:
	--repo                               owner/repo
	--callback                           pull_request_target | schedule | workflow_dispatch
	--lookback-days N                    Days to scan (bulk modes)
	--pending-label-age-days M           Days between reminders
    --remove                             Remove pending label (label command)

Logic:
	Add label when: no version label (regex vX(.Y)) and no pending label.
	Remind when: pending label present AND (no previous reminder OR last reminder older than M days).
	Marker: <!-- backport-pending-reminder -->

Exit codes: 0 success / 1 error.
"""

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

import click

ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
VERSION_LABEL_RE = re.compile(r"^v\d{1,2}(?:\.\d{1,2})?$")
BACKPORT_LABEL = "backport"
PENDING_LABEL_CANONICAL = "backport pending"
PENDING_LABEL_COLOR = "fff2bf"
GITHUB_API = "https://api.github.com"

CONFIG: Dict[str, str | None] = {
    "token": os.environ.get("BACKPORT_TOKEN"),
    "repo": os.environ.get("GITHUB_REPOSITORY"),  # owner/repo
    "dry_run": False,  # set by --dry-run
    "log_level": "INFO",  # INFO by default, set to DEBUG if --debug passed
    "command": None,  # set post-parse for logging
}


def is_dry_run() -> bool:
    return bool(CONFIG.get("dry_run"))


def require_mandatory_vars() -> None:
    """Validate critical environment / CLI inputs using CONFIG."""
    if not CONFIG.get("token") and not is_dry_run():
        raise RuntimeError("Missing BACKPORT_TOKEN from environment.")
    repo = CONFIG.get("repo")
    if not repo or not re.match(r"^[^/]+/[^/]+$", str(repo)):
        raise RuntimeError("Missing or invalid GITHUB_REPOSITORY. Either set it or pass --repo (owner/repo)")


def configure(dry_run: bool, debug: bool, command: str | None, repo: str | None) -> None:
    """Populate CONFIG, initialize logging, and validate required inputs.

    This centralizes setup so other entry points (tests, future subcommands)
    can reuse consistent initialization semantics.
    """
    CONFIG["dry_run"] = bool(dry_run)
    CONFIG["log_level"] = "DEBUG" if debug else "INFO"
    CONFIG["command"] = command
    if repo:
        CONFIG["repo"] = repo
    setup_logging(CONFIG["log_level"])
    require_mandatory_vars()


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


# ----------------------------- Shared HTTP Helpers -----------------------------
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
            logger.error(f"[label] PR #{pr.get('number','unknown')}: {e}")
            rc = 1
    return rc


# ----------------------------- Reminder Logic -----------------------------
COMMENT_MARKER_BASE = "<!-- backport-pending-reminder -->"  # static for detection
REMINDER_BODY = "A backport is pending for this PR.\n\n" "Please add an appropriate version label (e.g. v9.2)\n" "Thank you!"


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
        preview = body.splitlines()[0]
        logger.info(f"Post comment to PR #{number}: {preview}...")
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
class CallbackType(click.ParamType):
    name = "event"
    choices = ("pull_request_target", "schedule", "workflow_dispatch")

    def get_metavar(self, param):  # type: ignore[override]
        return "EVENT"

    def convert(self, value, param, ctx):  # type: ignore[override]
        if value in self.choices:
            return value
        self.fail(f"Invalid callback '{value}'. Choose from: {', '.join(self.choices)}", param, ctx)


@click.group(help="Backport utilities (label + remind)")
@click.option("--repo", required=False, metavar="OWNER/REPO", help="Override GITHUB_REPOSITORY (format: owner/repo)")
@click.option(
    "--callback",
    type=CallbackType(),
    required=True,
    metavar="EVENT",
    help="GitHub event context mode (EVENT: pull_request_target, schedule, workflow_dispatch)",
)
@click.option("--dry-run", is_flag=True, help="Simulate actions without modifying GitHub state")
@click.option("--debug", is_flag=True, help="Enable verbose debug logging")
@click.pass_context
def cli(ctx: click.Context, repo: str | None, callback: str, dry_run: bool, debug: bool):
    # Stash shared params into context; actual command name known later.
    ctx.ensure_object(dict)
    ctx.obj.update({"repo": repo, "callback": callback, "dry_run": dry_run, "debug": debug})


@cli.command(help="Add backport pending label to merged PRs without version label")
@click.option("--lookback-days", type=int, default=1, show_default=True, help="Days to look back when not pull_request_target")
@click.option("--remove", is_flag=True, help="Remove backport pending label")
@click.pass_context
def label(ctx: click.Context, lookback_days: int, remove: bool):
    params = ctx.obj
    configure(params.get("dry_run"), params.get("debug"), "label", params.get("repo"))
    callback = params.get("callback")
    prefetched = prefetch_prs(callback, lookback_days)
    raise SystemExit(run_label(prefetched, remove))


@cli.command(help="Post reminders on merged PRs still pending backport")
@click.option("--lookback-days", type=int, required=True, help="Days to look back for updated merged PRs")
@click.option("--pending-label-age-days", type=int, required=True, help="Days between reminders for the same PR")
@click.pass_context
def remind(ctx: click.Context, lookback_days: int, pending_label_age_days: int):
    params = ctx.obj
    configure(params.get("dry_run"), params.get("debug"), "remind", params.get("repo"))
    callback = params.get("callback")
    prefetched = prefetch_prs(callback, lookback_days)
    raise SystemExit(run_remind(prefetched, pending_label_age_days, lookback_days))


def prefetch_prs(callback: str, lookback_days: int) -> List[Dict[str, Any]]:
    if callback == "pull_request_target":
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


def main(argv: List[str] | None = None) -> int:
    try:
        cli.main(args=argv, prog_name="backport.py", standalone_mode=True)
        return 0
    except SystemExit as se:
        # Allow click to control exit codes
        return se.code
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

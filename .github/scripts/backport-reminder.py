import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Iterable, List
from urllib.parse import urlencode

ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
VERSION_LABEL_RE = re.compile(r"^v\d{1,2}(\.\d{1,2})?$")
PENDING_LABEL_CANONICAL = "Backport Pending"
COMMENT_MARKER = f"<!-- backport-pending-reminder every {os.environ.get('PENDING_LABEL_AGE_DAYS', '7')} days -->"
REMINDER_BODY = f"A backport is still pending for this merged PR. Please either:\n\n- Add an appropriate version label (e.g. v9.2), or\n- Remove the `{PENDING_LABEL_CANONICAL}` label if no backport will be performed.\n\nThank you!"
GITHUB_API = "https://api.github.com"

BACKPORT_TOKEN = os.environ.get("BACKPORT_TOKEN")


def gh_request(path: str, method: str = "GET", body: Dict[str, Any] | None = None, params: Dict[str, str] | None = None) -> Any:
    if params:
        path = f"{path}?{urlencode(params)}"
    url = f"{GITHUB_API}{path}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {BACKPORT_TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    try:
        with urllib.request.urlopen(req) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            txt = resp.read().decode(charset)
            if resp.status >= 300:
                raise RuntimeError(f"HTTP {resp.status}: {txt}")
            if not txt.strip():
                raise ValueError("Empty response")
            return json.loads(txt)
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"::error::HTTP {e.code} {e.reason} {err}", file=sys.stderr)
        raise
    except Exception as ex:
        print(f"::error::Unexpected error: {ex}", file=sys.stderr)
        raise


def list_prs(filter: str, since: dt.datetime) -> Iterable[Dict[str, Any]]:
    # Filter merged PRs updated since timeframe.
    # Format: repo:owner/name is:pr is:merged updated:>=YYYY-MM-DD
    q_date = since.strftime("%Y-%m-%d")
    page = 1
    while True:
        result = gh_request("/search/issues", params={"q": f"{filter} updated:>={q_date}", "per_page": "100", "page": str(page)})
        items = result.get("items", [])
        if not items:
            break
        for it in items:
            yield it
        if len(items) < 100:
            break
        page += 1
        time.sleep(0.25)


def get_pr(repo: str, number: int) -> Dict[str, Any]:
    return gh_request(f"/repos/{repo}/pulls/{number}")


def get_issue_comments(repo: str, number: int) -> List[Dict[str, Any]]:
    comments: List[Dict[str, Any]] = []
    page = 1
    while True:
        data = gh_request(f"/repos/{repo}/issues/{number}/comments", params={"per_page": "100", "page": str(page)})
        if not data:
            break
        comments.extend(data)
        if len(data) < 100:
            break
        page += 1
    return comments


def post_comment(repo: str, number: int, body: str) -> None:
    try:
        gh_request(f"/repos/{repo}/issues/{number}/comments", method="POST", body={"body": body})
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"::error::HTTP {e.code} {e.reason} {err}", file=sys.stderr)
        raise
    except Exception as ex:
        print(f"::error::Unexpected error: {ex}", file=sys.stderr)
        raise


def has_pending_label(labels: List[Dict[str, Any]]) -> bool:
    names_lower = {lbl.get("name", "").lower() for lbl in labels}
    return PENDING_LABEL_CANONICAL.lower() in names_lower


def last_reminder_time(comments: List[Dict[str, Any]]) -> dt.datetime | None:
    """Return timestamp of the newest reminder comment (first match in descending order)."""
    def comment_ts(c: Dict[str, Any]) -> dt.datetime:
        ts_raw = c.get("created_at") or c.get("updated_at")
        if not ts_raw:
            raise RuntimeError(f"Comment {c.get('id')}, {c.get('body')} missing both created_at and updated_at timestamps")
        return dt.datetime.strptime(ts_raw, ISO_FORMAT).replace(tzinfo=dt.timezone.utc)

    for c in sorted(comments, key=comment_ts, reverse=True):
        if COMMENT_MARKER in (c.get("body") or ""):
            return comment_ts(c)
    return None


"""Backport Pending reminder if label is present for more than X days.

Scans merged PRs updated within LOOKBACK_DAYS that still have the Backport
Pending label and posts an initial reminder (if none yet) or a follow‑up
reminder if the last one is older than PENDING_LABEL_AGE_DAYS.

Env:
    BACKPORT_TOKEN, GITHUB_REPOSITORY, LOOKBACK_DAYS, PENDING_LABEL_AGE_DAYS
"""


def main() -> int:
    # Initial sanity checks
    if not BACKPORT_TOKEN:
        print("::error::Missing BACKPORT_TOKEN", file=sys.stderr)
        return 1
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        print("::error::Invalid GITHUB_REPOSITORY", file=sys.stderr)
        return 1

    # Save and print the initial parameters
    lookback_days = int(os.environ.get("LOOKBACK_DAYS", "7"))
    age_days = int(os.environ.get("PENDING_LABEL_AGE_DAYS", "7"))
    now = dt.datetime.now(dt.timezone.utc)
    since = now - dt.timedelta(days=lookback_days)
    threshold = now - dt.timedelta(days=age_days)
    print(f"[reminder] Parameters: LOOKBACK_DAYS={lookback_days} PENDING_LABEL_AGE_DAYS={age_days}")
    print(f"[reminder] now={now.isoformat()} since(lookback start)={since.isoformat()} threshold(remind if before)={threshold.isoformat()}")

    # Process merged PRs updated since lookback_days
    for merged_pr in list_prs(f"repo:{repo} is:pr is:merged", since):
        try:
            labels = merged_pr.get("labels", [])
            # Skip if no pending label
            if not has_pending_label(labels):
                continue

            author = merged_pr.get("user", {}).get("login", "PR author")
            number = merged_pr.get("number") or int(merged_pr.get("url", "/").rstrip("/").split("/")[-1])
            comments = get_issue_comments(repo, number)
            prev_time = last_reminder_time(comments)
            # If pending label is present, check last reminder time.
            if prev_time is None:
                post_comment(repo, number, f"{COMMENT_MARKER}\n@{author}\n{REMINDER_BODY}")
                print(f"[reminder]  PR #{number}: Posted initial reminder (no prior marker)")
            elif prev_time < threshold:
                post_comment(repo, number, f"{COMMENT_MARKER}\n@{author}\n{REMINDER_BODY}")
                delta = (threshold - prev_time).days
                print(f"[reminder]  PR #{number}: Posted follow-up reminder, delta {delta}")
            else:
                print(f"[reminder]  PR #{number}: Cooling period not elapsed ({prev_time} > threshold) -> skip")
        except Exception as ex:
            # Error handling is per-PR to continue processing others, as this job makes the necessary API calls to avoid action duplication.
            print(f"::error:: PR #{number}: Unexpected error: {ex}", file=sys.stderr)
            continue
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

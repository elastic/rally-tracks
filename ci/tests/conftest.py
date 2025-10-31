"""Pytest configuration and fixtures for testing the backport CLI.

Provides:
  - Dynamic loading of the `backport.py` module (so no package __init__ files required).
  - An injectable GitHub API mock (`gh_mock`) that records calls and returns
	predefined responses or raises exceptions.
  - Helper fixtures for creating synthetic PR payloads and reminder comments.
  - A convenience fixture to run `configure()` with a minimal argparse.Namespace.

Usage examples in tests:

  def test_needs_pending_label(backport_mod, pr_no_labels):
	  assert backport_mod.needs_pending_label(pr_no_labels)

  def test_label_api_called(backport_mod, gh_mock, pr_versioned):
	  gh_mock.add('/repos/test/repo/labels/backport%20pending', method='GET', response={})  # label exists
	  gh_mock.add('/repos/test/repo/issues/42/labels', method='POST', response={'ok': True})
	  backport_mod.add_label(42, backport_mod.PENDING_LABEL)
	  assert any('/repos/test/repo/issues/42/labels' in c['path'] for c in gh_mock.calls)

Note: We treat paths exactly as provided to `gh_request` after query param expansion.
If you register a route with query parameters, include the full `path?query=..` string.
"""

from __future__ import annotations

import argparse
import os
import json
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlencode
import importlib.util

import pytest


# ----------------------- Environment / Config ------------------------
@pytest.fixture(scope="session", autouse=True)
def set_env() -> None:
    """Session-level mandatory environment variables prior to any module use.

    Can't use the function-scoped `monkeypatch` fixture from a session scope, so
    we set values directly on os.environ here.
    """
    os.environ["BACKPORT_TOKEN"] = "dummy-token"
    os.environ["GITHUB_REPOSITORY"] = "test/repo"


@pytest.fixture()
def args_namespace() -> argparse.Namespace:
    """Return a baseline argparse.Namespace similar to parse_args() output."""
    return argparse.Namespace(
        dry_run=False,
        verbose=0,
        quiet=0,
        command=None,
        repo="test/repo",
        pr_mode=False,
        lookback_days=7,
        pending_label_age_days=14,
        remove=False,
    )


# --------------------------- Module Loader ---------------------------
@pytest.fixture(scope="session")
def backport_path() -> Path:
    """Return the path to the backport.py script without referring
    to the repository root. This keeps all CI script testing self-contained.
    """
    ci_root = Path(__file__).resolve().parents[1]
    path = ci_root / "scripts" / "backport.py"
    if not path.exists():
        raise FileNotFoundError(f"Could not locate backport.py at {path}")
    return path


@pytest.fixture(scope="function")
def backport_mod(backport_path):
    """Dynamically load the backport CLI module from ci/scripts."""
    spec = importlib.util.spec_from_file_location("backport", backport_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    if spec.loader is None:
        raise RuntimeError("Failed to create loader for backport module")
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


# --------------------------- GitHub Mock -----------------------------
@dataclass
class RouteResponse:
    status: int
    json: dict[str, Any] | list[dict[str, Any]]
    exception: BaseException | None = None

@dataclass
class CallRecord:
    path: str
    method: str
    body: dict[str, Any] | None
    params: dict[str, str] | None


class GitHubMock:
    """Approximating GitHub REST semantics.

    Routes: Each route is a predefined (path, HTTP method) pair with an associated fake
    response (JSON, status code, optional injected exception). It models individual
    GitHub REST API endpoints the code under test might call.  Registering routes lets
    tests declare exactly which API interactions are expected and what data or error
    should be returned, without making real network calls.

    Calls list: Every time the mocked gh_request is invoked, the mock appends an entry 
    (path, method, body, params) to calls. 
    Tests use this list to assert:
     * That expected endpoints were hit (presence/order/count).
     * That no unexpected endpoints were called (empty list in dry‑run cases).
     * That request bodies or query parameters match what the logic should send.

    In short: 
    - Routes define allowed interactions
    - Calls record actual interactions for verification.

    Routes are matched by fully expanded path (including query string) and uppercased method.
    """

    def __init__(self) -> None:
        self._routes: dict[tuple[str, str], RouteResponse] = {}
        self.calls: list[CallRecord] = []

    # -------------- Registration --------------
    def add(
        self,
        path: str,
        method: str = "GET",
        response: dict[str, Any] | list[dict[str, Any]] = {},
        status: int = 200,
        exception: BaseException | None = None,
    ) -> None:
        """Register a route.

        Parameters:
          path: API path exactly as gh_request would see
          method: HTTP method
          response: JSON-serializable object returned to caller
          status: HTTP status code (>=400 will raise RuntimeError automatically)
          exception: If provided, raised instead of using status/response
        """
        self._routes[(path, method.upper())] = RouteResponse(status=status, json=response, exception=exception)

    # -------------- Invocation --------------
    def __call__(
        self,
        path: str,
        method: str = "GET",
        body: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
    ) -> Any:
        if params:
            path = f"{path}?{urlencode(params)}"
        key = (path, method.upper())
        self.calls.append(CallRecord(
            path=path,
            method=method.upper(),
            body=deepcopy(body),
            params=deepcopy(params),
        ))
        if key not in self._routes:
            raise AssertionError(
                f"Unexpected GitHub API call: {key}. "
                f"Registered routes: {list(self._routes.keys())}"
            )
        route = self._routes[key]
        if route.exception:
            raise route.exception
        if route.status >= 400:
            raise RuntimeError(f"HTTP {route.status}: {route.json}")
        return deepcopy(route.json)

    def add_label_exists(self, repo: str, label: str, *, color: str = "fff2bf") -> None:
        encoded = label.replace(' ', '%20')
        self.add(f"/repos/{repo}/labels/{encoded}", response={"name": label, "color": color})

    def add_label_create(self, repo: str, label: str, *, color: str = "fff2bf") -> None:
        self.add(f"/repos/{repo}/labels", method="POST", response={"name": label, "color": color})

    def add_issue_comments_pages(self, repo: str, number: int, pages: list[list[dict[str, Any]]]) -> None:
        for idx, comments in enumerate(pages, start=1):
            self.add(
                f"/repos/{repo}/issues/{number}/comments?per_page=100&page={idx}",
                response=comments,
            )

    def add_search_issues(self, query: str, pages: list[list[dict[str, Any]]]) -> None:
        # Each page path will include per_page + page param
        for page_num, items in enumerate(pages, start=1):
            self.add(
                f"/search/issues?q={query}&per_page=100&page={page_num}",
                response={"items": items},
            )

    def clear(self) -> None:
        self._routes.clear()
        self.calls.clear()
    
    # -------------- Assertion (order only) --------------
    def assert_calls_in_order(self, *paths: str, strict: bool = False) -> None:
        """Assert that the provided sequence of call paths appears in order.

        Behavior:
          * No paths provided => assert no calls were made.
          * With paths => each must appear in the recorded calls in the given order.
          * strict=True => number of recorded calls must equal number of provided paths.
        """
        if not paths:
            if self.calls:
                raise AssertionError(
                    f"Expected no GitHub calls, saw {len(self.calls)}: "
                    f"{[(c.method, c.path) for c in self.calls]}"
                )
            return
        call_paths = [c.path for c in self.calls]
        pos = 0
        for expected in paths:
            try:
                idx = call_paths.index(expected, pos)
            except ValueError as e:
                raise AssertionError(
                    f"Expected path in order not found: {expected}. Remaining calls: {call_paths[pos:]}"
                ) from e
            pos = idx + 1
        if strict and len(call_paths) != len(paths):
            raise AssertionError(
                f"Strict order mismatch: expected exactly {len(paths)} calls, saw {len(call_paths)}: {call_paths}"
            )


@pytest.fixture()
def gh_mock(backport_mod, monkeypatch: pytest.MonkeyPatch) -> GitHubMock:
    """Fixture that patches `backport_mod.gh_request` with a controllable mock.

    Use `gh_mock.add(...)` to declare responses before invoking code under test.

    By replacing backport_mod.gh_request with GitHubMock, each test can:
    - Declare exactly which endpoints should be called (via add()).
    - Control payloads and error codes deterministically.
    """
    mock = GitHubMock()
    monkeypatch.setattr(backport_mod, "gh_request", mock)
    return mock


# --------------------------- PR Data Helpers -------------------------
def make_pr(labels: list[str], number: int = 42, merged: bool = True) -> dict[str, Any]:
    """Lightweight helper for ad-hoc PR dict construction in tests that
    aren't using PRCase tables yet.

    Prefer `PRCase.pr_info` for table-driven scenarios; this remains for
    legacy single-off tests.
    """
    return {
        "number": number,
        "merged": merged,
        "merged_at": "2025-10-01T12:00:00Z" if merged else None,
        "labels": [{"name": l} for l in labels],
    }


# --------------------------- Event Payload ---------------------------
@pytest.fixture()
def event_file(tmp_path) -> Path:
    """Create a temporary GitHub event JSON mimicking pull_request payload."""
    payload = {"pull_request": make_pr(labels=[])}
    path = tmp_path / "event.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


@pytest.fixture()
def set_event(monkeypatch: pytest.MonkeyPatch, event_file) -> None:
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_file))


# ------------------------- Param Helpers -----------------------------
@pytest.fixture()
def make_args(args_namespace: argparse.Namespace) -> Callable[..., argparse.Namespace]:
    """Factory to clone and override the baseline args namespace for specific tests."""

    def _make(**overrides: Any) -> argparse.Namespace:
        data = vars(args_namespace).copy()
        data.update(overrides)
        return argparse.Namespace(**data)

    return _make

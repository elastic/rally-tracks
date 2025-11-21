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
	  gh_mock.add(f'repos/{TEST_REPO}/labels/backport%20pending', method='GET', response={})  # label exists
	  gh_mock.add(f'repos/{TEST_REPO}/issues/42/labels', method='POST', response={'ok': True})
	  backport_mod.add_pull_request_label(42, backport_mod.PENDING_LABEL)
	  assert any(f'repos/{TEST_REPO}/issues/42/labels' in c['path'] for c in gh_mock.calls)

Note: We treat paths exactly as provided to `gh_request` after query param expansion.
If you register a route with query parameters, include the full `path?query=..` string.
"""

import datetime as dt
import fnmatch
import importlib.util
import os
import sys
from copy import deepcopy
from dataclasses import dataclass
from os.path import dirname, join
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import pytest

from github_ci_tools.scripts import backport
from github_ci_tools.tests.utils import NOW, TEST_REPO, convert_str_to_date


# ----------------------- Environment / Config ------------------------
@pytest.fixture(autouse=True)
def set_env() -> None:
    """Session-level mandatory environment variables prior to any module use.

    Can't use the function-scoped `monkeypatch` fixture from a session scope, so
    we set values directly on os.environ here.
    """
    os.environ["BACKPORT_TOKEN"] = "dummy-token"
    os.environ["GITHUB_REPOSITORY"] = TEST_REPO


# --------------------------- Module Loader ---------------------------
@pytest.fixture(scope="function")
def backport_mod(monkeypatch) -> Any:
    module = backport
    fixed = convert_str_to_date(NOW)

    class FixedDateTime(dt.datetime):
        @classmethod
        def now(cls, tz=None):  # noqa: D401
            # Always return an aware datetime. If tz is provided, adjust; otherwise keep UTC.
            if tz is None:
                return fixed
            return fixed.astimezone(tz)

    monkeypatch.setattr(module.dt, "datetime", FixedDateTime)
    return module


# --------------------------- GitHub Mock -----------------------------
@dataclass
class MockRouteResponse:
    status: int
    json: dict[str, Any] | list[dict[str, Any]]
    exception: BaseException | None = None


@dataclass
class MockCallRecord:
    method: str
    path: str
    body: dict[str, Any] | None
    params: dict[str, str] | None


class GitHubMock:
    """Approximating GitHub REST semantics.

    Routes: Each route is a predefined (path, HTTP method) pair with an associated
    response for simulation (JSON, status code, exception, object types). It models
    individual GitHub REST API endpoints the code under test might call. Registering
    routes lets tests declare exactly which API interactions are expected and which data
    or error should be returned, without making real network calls.

    Calls list: Every time the mocked gh_request is invoked, the mock appends an entry
    (path, method, body, params) to calls. Tests use this list to assert:
        * That expected endpoints were hit (presence/order/count).
        * That request bodies or query parameters match what the logic should send.

    In short:
        - Routes define allowed interactions
        - Calls record actual interactions.
        - Assertion helper to verify expected vs actual behavior.

    Routes are matched by fully expanded path and uppercased method.

    Wildcard / glob support:
        Register paths containing the literal sequence '...' (three dots). Each '...'
        becomes a glob wildcard (*).
            For example: '/search/issues?q=a_string...repo...merged...updated...end_string'
              -> Glob pattern: '/search/issues?q=a_string*repo*merged*updated*end_string*'
              -> Matches any path that starts with 'a_string', contains 'repo', 'merged', 'updated'
                 in that order, and ends with 'end_string'.
    """

    def __init__(self) -> None:
        self._routes: dict[tuple[str, str], MockRouteResponse] = {}
        self._glob_routes: list[tuple[str, str, str, MockRouteResponse]] = []  # (METHOD, original, glob_pattern, response)
        self.calls: list[MockCallRecord] = []

    # -------------- Registration ------------
    def add(
        self,
        method: str = "GET",
        path: str = "/repos",
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
        m = method.upper()
        route_resp = MockRouteResponse(status=status, json=response, exception=exception)
        if "..." in path:
            parts = path.split("...")
            glob_pattern = "*".join(parts)
            if not path.endswith("..."):
                glob_pattern += "*"
            self._glob_routes.append((m, path, glob_pattern, route_resp))
        else:
            self._routes[(m, path)] = route_resp

    # -------------- Invocation --------------
    def __call__(
        self,
        method: str = "GET",
        path: str = "repos",
        body: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
    ) -> Any:
        if params:
            path = f"{path}?{urlencode(params)}"
        path = f"/{path}"
        key = (method.upper(), path)

        self.calls.append(
            MockCallRecord(
                method=method.upper(),
                path=path,
                body=deepcopy(body),
                params=deepcopy(params),
            )
        )
        if key not in self._routes:
            # Register paths containing several literal sequences '...' which become glob wildcards (*).
            route = None
            if self._glob_routes:
                for m, original, glob_pattern, resp in self._glob_routes:
                    if m != method.upper():
                        continue
                    if fnmatch.fnmatchcase(path, glob_pattern):
                        route = resp
                        break
            if route is None:
                raise AssertionError(
                    f"Unexpected GitHub API call: {key}. Registered exact: {list(self._routes.keys())} glob: {[(method, orig) for method,orig,_,_ in self._glob_routes]}"
                )
        else:
            route = self._routes[key]

        if route.exception:
            raise route.exception
        if route.status >= 400:
            raise RuntimeError(f"HTTP {route.status}: {route.json}")
        return deepcopy(route.json)

    # -------------- Assertion ---------------
    def assert_calls_in_order(self, *expected: tuple[str, str], strict: bool = True) -> None:
        """
        Assert that the provided sequence of (HTTP_METHOD, full_path) tuples appears
        in order. When strict=True (default), the recorded calls must match exactly
        (same length and element-wise equality). When strict=False, the expected
        sequence must appear as an ordered subsequence within the recorded calls.
        """
        actual = [(c.method, c.path) for c in self.calls]
        if not expected:
            if actual:
                raise AssertionError(f"Expected no GitHub calls, but saw {len(actual)}: {actual}")
            return

        def glob_match(exp: tuple[str, str], act: tuple[str, str]) -> bool:
            exp_m, exp_p = exp
            act_m, act_p = act
            if exp_m != act_m:
                return False
            if "..." in exp_p:
                parts = exp_p.split("...")
                glob_pattern = "*".join(parts)
                if not exp_p.endswith("..."):
                    glob_pattern += "*"
                return fnmatch.fnmatchcase(act_p, glob_pattern)
            else:
                return exp_p == act_p

        check = True
        if strict:
            # Build a small diff aid
            lines = ["Strict order mismatch:"]
            for i, (exp, act) in enumerate(zip(expected, actual)):
                max_len = max(len(actual), len(expected))
                for i in range(max_len):
                    exp = expected[i] if i < len(expected) else ("<none>", "<none>")
                    act = actual[i] if i < len(actual) else ("<none>", "<none>")
                    if exp and act and (exp == act or glob_match(exp, act)):
                        marker = "OK"
                    else:
                        marker = "!!"
                        check = False
                    lines.append(f"[{i}] exp={exp} act={act} {marker}")
            if not check:
                raise AssertionError("\n".join(lines))
            return

        # Relaxed subsequence check
        it = iter(actual)
        for exp in expected:
            if not any(expected == act or glob_match(exp, act) for act in it):
                check = False
                raise AssertionError(f"Expected {expected} not found in actual calls: {actual}")

    # -------------- Convenience --------------
    @property
    def calls_list(self) -> list[tuple[str, str]]:
        """Return the list of recorded calls as (method, path) tuples for convenience."""
        return [(c.method, c.path) for c in self.calls]


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


# --------------------------- Event Payload ---------------------------
@pytest.fixture()
def event_file(tmp_path, monkeypatch) -> Path:
    """Create a temporary GitHub event JSON."""
    path = tmp_path / "event.json"
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(path))
    return path

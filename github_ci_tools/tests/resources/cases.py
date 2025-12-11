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

from dataclasses import dataclass, field, asdict
from typing import Any, Callable, TypeVar

import pytest

from github_ci_tools.tests.utils import (
    STATIC_ROUTES,
    TEST_REPO,
    Comment,
    GHRoute,
    Label,
)


@dataclass
class PullRequestCase:
    """Represents a single pull request test scenario. Also used to hold PR state.

    Fields:
      labels: Simple list of label names.
      comments: Optional list of issue comment dicts (each with at least 'body' and 'created_at').
                Used for testing reminder logic without separate fixtures.
      number / merged / merged_at: Basic PR metadata.
      remove: Flag you can pass through to label command tests.
    """

    number: int = 42
    labels: list[Label] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    needs_pending: bool = False
    needs_reminder: bool = False
    backport_pending_in_labels: bool = False
    merged: bool = True
    merged_at: str | None = None
    remove: bool = False  # To select PRs for label removal.

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, dict):
            other = PullRequestCase(**other)
        return (
            self.number == other.number
            and self.labels == other.labels
            and self.merged == other.merged
            and self.merged_at == other.merged_at
        )


@dataclass
class RepoCase:
    """Repository-level label scenario. Also used to hold the repository state.

    repo_labels:    Names of labels currently defined in the repository.
                    Used to drive repo_needs_pending_label / ensure_backport_pending_label behavior.
    create_raises:  Simulate a failure when attempting to create the label.
    """

    name: str = TEST_REPO
    prs: list[PullRequestCase] = field(default_factory=list)
    repo_labels: list[Label] = field(default_factory=list)
    needs_pending: bool = False
    create_raises: bool = False

    @property
    def repo(self) -> str:
        return self.name

    def register(self, gh_mock: Any) -> None:  # 'Any' to avoid circular import of GitHubMock
        """Register all declared routes on the provided gh_mock instance."""
        static_get_labels = STATIC_ROUTES["get_labels"]
        static_create_pending_label = STATIC_ROUTES["create_pending_label"]
        existing = [{"name": label.name, "color": label.color} for label in self.repo_labels]

        gh_mock.add("GET", static_get_labels.path, response=existing)
        if self.needs_pending:
            if self.create_raises:
                gh_mock.add(static_create_pending_label.method, static_create_pending_label.path, exception=RuntimeError("fail create"))
            else:
                gh_mock.add(
                    static_create_pending_label.method, static_create_pending_label.path, response=static_create_pending_label.response
                )
        for pr in self.prs:
            gh_mock.add(
                "GET",
                f"/repos/{self.name}/pulls/{pr.number}",
                response=asdict(pr),
            )


# ---------------- Unified Interaction Case -----------------
@dataclass
class GHInteractionCase:
    """Unified scenario combining PR / Repo data and expected GitHub interactions.

    This is an optional higher-level abstraction that can replace separate
    PullRequestCase + ad-hoc route registration in tests. It is intentionally kept
    lightweight so existing tests can migrate incrementally.

    Fields:
      prs: List of PullRequestCase objects (supporting multi-PR scenarios like bulk searches).
      repo: RepoCase (repository label logic) - unused for current label tests.
      routes: Pre-declared list of GHRoute entries to register on gh_mock.
      expected_order: Ordered list of (method, path) tuples expected to appear (subsequence); may be empty.
      strict: When True, assert call count equals expected_order length.
    """

    repo: RepoCase = field(default_factory=RepoCase)
    routes: list[GHRoute] = field(default_factory=list)
    lookback_days: int = 7
    pending_reminder_age_days: int = 7
    expected_prefetch_prs: list[dict[str, Any]] | None = field(default_factory=list)
    expected_order: list[tuple[str, str]] = field(default_factory=list)
    strict: bool = True
    raises_error: type[Exception] | None = None

    def register(self, gh_mock: Any) -> None:  # 'Any' to avoid circular import of GitHubMock
        """Register all declared routes on the provided gh_mock instance."""
        if self.repo:
            self.repo.register(gh_mock)
        for r in self.routes:
            gh_mock.add(method=r.method, path=r.path, response=r.response, status=r.status, exception=r.exception)


# ---------------- Backport CLI Definitions -----------------
@dataclass
class BackportCliCase:
    """Table-driven CLI scenario data container."""

    argv: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=lambda: {"BACKPORT_TOKEN": "tok", "GITHUB_REPOSITORY": TEST_REPO})
    delete_env: list[str] = field(default_factory=list)
    expect_parse_exit: bool = False
    expect_require_error_substr: str | None = None
    expected_config: dict[str, Any] = field(default_factory=dict)
    expected_args: dict[str, Any] = field(default_factory=dict)
    expected_log_level: int | None = None  # When None, log level assertion is skipped.
    gh_interaction: GHInteractionCase = field(default_factory=GHInteractionCase)
    raises_error: type[Exception] | None = None


C = TypeVar("C")


def cases(arg_name: str = "case", **table: C) -> Callable:
    """cases defines a decorator wrapping `pytest.mark.parametrize` to run a test against multiple cases.

    The purpose of this decorator is to create table-driven unit tests (https://go.dev/wiki/TableDrivenTests).

    param arg_name: the name of the parameter used for the input table (by default is 'case').
    :param table:
        a dictionary of per use case entries that represent the test input table. It typically contains
        either input parameters and configuration for initial test case status (or fixtures)
    :return: a test method decorator.

    Usage:
        @cases(
           no_labels=PullRequestCase(labels=[], needs_pending=True),
        )
        def test_create(case):
            assert backport_mod.pr_needs_pending_label(backport_mod.PRInfo.from_dict(asdict(case))) is case.needs_pending
    """
    return pytest.mark.parametrize(argnames=arg_name, argvalues=list(table.values()), ids=list(table.keys()))

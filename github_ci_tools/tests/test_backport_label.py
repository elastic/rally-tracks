from dataclasses import asdict

import pytest

from github_ci_tools.tests.resources.case_registry import (
    GHInteractAction,
    build_gh_routes_labels,
    case_by_number,
    expected_actions_for_prs,
    expected_actions_for_repo,
    select_pull_requests,
)
from github_ci_tools.tests.resources.cases import (
    GHInteractionCase,
    PullRequestCase,
    RepoCase,
    cases,
)
from github_ci_tools.tests.utils import LABELS, STATIC_ROUTES


@cases(
    exists_dont_create=RepoCase(repo_labels=LABELS["pending"]),
    no_label_repo_creates=RepoCase(repo_labels=[], needs_pending=True),
    no_label_but_gh_error=RepoCase(repo_labels=[], needs_pending=True, create_raises=True),
    ignore_duplicate_pending=RepoCase(repo_labels=LABELS["pending_duplicate"]),
    only_backport_label_creates=RepoCase(repo_labels=LABELS["backport"], needs_pending=True),
    labels_with_pending_typo_creates=RepoCase(repo_labels=LABELS["pending_typo"], needs_pending=True),
    labels_with_backport_typo_creates=RepoCase(repo_labels=LABELS["backport_typo"], needs_pending=True),
)
def test_repo_ensure_backport_pending_label(backport_mod, gh_mock, caplog, case: RepoCase):
    """Ensure creation only when PENDING_LABEL is strictly absent."""
    static_get_labels = STATIC_ROUTES["get_labels"]
    static_create_pending_label = STATIC_ROUTES["create_pending_label"]
    existing = [{"name": label.name, "color": label.color} for label in case.repo_labels]

    gh_mock.add("GET", static_get_labels.path, response=existing)

    if case.needs_pending:
        if case.create_raises:
            gh_mock.add(
                static_create_pending_label.method, static_create_pending_label.path, exception=RuntimeError("Could not create label")
            )
            with pytest.raises(RuntimeError, match=backport_mod.COULD_NOT_CREATE_LABEL_ERROR):
                backport_mod.ensure_backport_pending_label()
            assertions = [
                *expected_actions_for_repo(GHInteractAction.REPO_GET_LABELS),
                (static_create_pending_label.method, static_create_pending_label.path),
            ]
            gh_mock.assert_calls_in_order(*assertions)
            return
        else:
            gh_mock.add(static_create_pending_label.method, static_create_pending_label.path, response=static_create_pending_label.response)
            backport_mod.ensure_backport_pending_label()
    else:
        backport_mod.ensure_backport_pending_label()

    assertions = [*expected_actions_for_repo(GHInteractAction.REPO_GET_LABELS)]
    if case.needs_pending and not case.create_raises:
        assertions.append((static_create_pending_label.method, static_create_pending_label.path))
    gh_mock.assert_calls_in_order(*assertions)


@cases(
    add_to_single_pr_with_no_label=GHInteractionCase(
        repo=RepoCase(prs=[case_by_number(101)]),
        routes=[
            *build_gh_routes_labels("POST", [case_by_number(101)]),
        ],
    ),
    add_pull_request_label_only_to_those_needs_pending=GHInteractionCase(
        repo=RepoCase(prs=select_pull_requests(remove=False)),
        routes=[*build_gh_routes_labels("POST", select_pull_requests(remove=False))],
    ),
    remove_pull_request_label_only_for_those_that_has_pending=GHInteractionCase(
        repo=RepoCase(prs=select_pull_requests(remove=True)),
        routes=[*build_gh_routes_labels("DELETE", select_pull_requests(remove=True))],
    ),
)
def test_label_logic(backport_mod, gh_mock, case: GHInteractionCase):
    """Test of the exact logic as in run_label."""
    case.register(gh_mock)
    for pr in case.repo.prs:
        # Test of the exact logic as in run_label
        pr_info = backport_mod.PRInfo.from_dict(asdict(pr))
        assert backport_mod.pr_needs_pending_label(pr_info) is pr.needs_pending

        if pr.remove:
            backport_mod.remove_pull_request_label(pr.number, backport_mod.PENDING_LABEL)
            case.expected_order += expected_actions_for_prs(GHInteractAction.PR_REMOVE_PENDING_LABEL, [case_by_number(pr.number)])
        elif pr.needs_pending:
            backport_mod.add_pull_request_label(pr.number, backport_mod.PENDING_LABEL)
            case.expected_order += expected_actions_for_prs(GHInteractAction.PR_ADD_PENDING_LABEL, [case_by_number(pr.number)])
    gh_mock.assert_calls_in_order(*case.expected_order)


@cases(
    no_version_labels_needs_pending=PullRequestCase(number=501, labels=[], needs_pending=True),
    single_version_label_no_pending=PullRequestCase(number=502, labels=LABELS["versioned"], needs_pending=False),
    multiple_version_labels_no_pending=PullRequestCase(number=503, labels=LABELS["multiple_versioned"], needs_pending=False),
    single_version_with_other_labels_no_pending=PullRequestCase(
        number=504, labels=[*LABELS["versioned"], LABELS["backport_typo"][0]], needs_pending=False
    ),
    multiple_versions_with_other_labels_no_pending=PullRequestCase(
        number=505, labels=[*LABELS["multiple_versioned_with_other"]], needs_pending=False
    ),
    has_backport_label_no_pending=PullRequestCase(number=506, labels=LABELS["backport"], needs_pending=False),
    has_pending_label_no_pending=PullRequestCase(number=507, labels=LABELS["pending"], needs_pending=False),
    has_both_version_and_pending_no_pending=PullRequestCase(number=508, labels=LABELS["versioned_pending"], needs_pending=False),
)
def test_version_label_scenarios(backport_mod, case: PullRequestCase):
    """Test pr_needs_pending_label with various version label configurations.

    Covers:
    - PRs with no version labels (should need pending)
    - PRs with single version label (should NOT need pending)
    - PRs with multiple version labels (should NOT need pending)
    """
    pr_info = backport_mod.PRInfo.from_dict(asdict(case))
    assert backport_mod.pr_needs_pending_label(pr_info) is case.needs_pending

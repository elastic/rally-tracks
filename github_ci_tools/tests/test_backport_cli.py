import logging
import sys
from dataclasses import asdict

import pytest

from github_ci_tools.tests.resources.case_registry import (
    GHInteractAction,
    build_gh_routes_labels,
    build_gh_routes_repo,
    case_by_number,
    expected_actions_for_prs,
    expected_actions_for_repo,
    select_pull_requests,
    select_pull_requests_by_lookback,
)
from github_ci_tools.tests.resources.cases import (
    BackportCliCase,
    GHInteractionCase,
    RepoCase,
    cases,
)
from github_ci_tools.tests.utils import TEST_REPO, GHRoute


@cases(
    label_basic=BackportCliCase(
        argv=["backport.py", "--dry-run", "-vv", "label", "--lookback-days", "30"],
        env={"BACKPORT_TOKEN": "tok"},
        expected_args={"command": "label", "lookback_days": 30, "lookback_mode": "updated", "dry_run": True, "verbose": 2},
        expected_config={"repo": TEST_REPO, "dry_run": True, "command": "label", "verbose": 2, "quiet": 0},
        expected_log_level=logging.NOTSET,
    ),
    label_default_lookback=BackportCliCase(
        argv=["backport.py", "label"],
        env={"BACKPORT_TOKEN": "tok"},
        expected_args={"command": "label", "lookback_days": 7},
        expected_config={"repo": TEST_REPO, "command": "label", "verbose": 0, "quiet": 0},
        expected_log_level=logging.INFO,
    ),
    label_override_lookback=BackportCliCase(
        argv=["backport.py", "label", "--lookback-days", "45"],
        env={"BACKPORT_TOKEN": "tok"},
        expected_args={"command": "label", "lookback_days": 45},
        expected_config={"repo": TEST_REPO, "command": "label", "verbose": 0, "quiet": 0},
        expected_log_level=logging.INFO,
    ),
    remind_basic=BackportCliCase(
        argv=["backport.py", "remind", "--lookback-days", "10"],
        env={"BACKPORT_TOKEN": "tok", "GITHUB_REPOSITORY": TEST_REPO},
        expected_args={"command": "remind", "lookback_days": 10, "lookback_mode": "updated"},
        expected_config={"repo": TEST_REPO, "command": "remind", "verbose": 0, "quiet": 0},
        expected_log_level=logging.INFO,
    ),
    remind_default_pending_age=BackportCliCase(
        argv=["backport.py", "remind"],
        env={"BACKPORT_TOKEN": "tok"},
        expected_args={"command": "remind", "lookback_days": 7},
        expected_config={"repo": TEST_REPO, "command": "remind", "verbose": 0, "quiet": 0},
        expected_log_level=logging.INFO,
    ),
    missing_command=BackportCliCase(
        argv=["backport.py"],
        env={"BACKPORT_TOKEN": "tok", "GITHUB_REPOSITORY": "acme/repo"},
        expect_parse_exit=True,
    ),
    missing_token=BackportCliCase(
        argv=["backport.py", "label"],
        delete_env=["BACKPORT_TOKEN"],
        expect_require_error_substr="Missing BACKPORT_TOKEN",
    ),
    missing_repo=BackportCliCase(
        argv=["backport.py", "label"],
        delete_env=["GITHUB_REPOSITORY"],
        expect_require_error_substr="Missing or invalid GITHUB_REPOSITORY",
    ),
)
def test_backport_cli_parsing(backport_mod, monkeypatch, case: BackportCliCase):
    # Environment setup
    for k, v in case.env.items():
        monkeypatch.setenv(k, v)
    for k in case.delete_env:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(sys, "argv", case.argv)

    if case.expect_parse_exit:
        with pytest.raises(SystemExit):
            backport_mod.parse_args()
        return

    args = backport_mod.parse_args()

    # Validate argparse Namespace expectations
    for key, expected in case.expected_args.items():
        assert getattr(args, key) == expected

    # Attempt configure (which calls require_mandatory_vars)
    if case.expect_require_error_substr:
        with pytest.raises(RuntimeError) as exc:
            backport_mod.configure(args)
        assert case.expect_require_error_substr in str(exc.value)
        return

    backport_mod.configure(args)

    # Validate CONFIG state
    for key, expected in case.expected_config.items():
        assert getattr(backport_mod.CONFIG, key) == expected

    # Optional log level assertion provided by test case (error cases may skip)
    if case.expected_log_level is not None:
        if isinstance(case.expected_log_level, int):
            assert backport_mod.CONFIG.log_level == case.expected_log_level
        else:
            case.expected_log_level(backport_mod)


@cases(
    merged_recently=GHInteractionCase(
        repo=RepoCase(prs=[case_by_number(101)]),
        lookback_days=7,
        expected_prefetch_prs=[asdict(case_by_number(101))],
    ),
    merged_old=GHInteractionCase(
        repo=RepoCase(prs=[case_by_number(108)]),
        lookback_days=10,
        expected_prefetch_prs=None,
    ),
    merged_really_old_but_still_in_window=GHInteractionCase(
        repo=RepoCase(prs=[case_by_number(301)]),
        lookback_days=1200,
        expected_prefetch_prs=[asdict(case_by_number(301))],
    ),
    unmerged_raises_error=GHInteractionCase(
        repo=RepoCase(prs=[case_by_number(202)]),
        lookback_days=1200,
        expected_prefetch_prs=None,
        raises_error=RuntimeError,
    ),
)
def test_prefetch_prs_in_single_pr_mode(backport_mod, gh_mock, case: GHInteractionCase):
    case.register(gh_mock)
    backport_mod.CONFIG.repo = TEST_REPO

    # Prefetched PRs must be one, None or raise error
    if case.raises_error:
        with pytest.raises(case.raises_error):
            prefetched_prs = backport_mod.prefetch_prs(
                pr_number=case.repo.prs[0].number, lookback_days=case.lookback_days, lookback_mode="updated"
            )
        return
    prefetched_prs = backport_mod.prefetch_prs(pr_number=case.repo.prs[0].number, lookback_days=case.lookback_days, lookback_mode="updated")
    if prefetched_prs:
        assert len(prefetched_prs) == 1
    prefetched_pr = prefetched_prs if prefetched_prs else None

    assert prefetched_pr == case.expected_prefetch_prs


@cases(
    adds_repo_label_and_labels_only_within_lookback=BackportCliCase(
        argv=["backport.py", "label"],
        gh_interaction=GHInteractionCase(
            repo=RepoCase(repo_labels=[], prs=select_pull_requests()),
            lookback_days=7,
            expected_prefetch_prs=[asdict(pr) for pr in select_pull_requests_by_lookback(7)],
            routes=[
                GHRoute(
                    path=f"/search/issues...merged...updated...",
                    method="GET",
                    response={"items": [asdict(pr) for pr in select_pull_requests_by_lookback(7)]},
                ),
                *build_gh_routes_labels("GET", select_pull_requests_by_lookback(7)),
                *build_gh_routes_labels("POST", select_pull_requests_by_lookback(7)),
                *build_gh_routes_repo(),
            ],
            expected_order=[
                *expected_actions_for_prs(GHInteractAction.ITER_PRS, select_pull_requests_by_lookback(7)),
                *expected_actions_for_repo(GHInteractAction.REPO_GET_LABELS),
                *expected_actions_for_repo(GHInteractAction.REPO_ADD_LABEL),
                *expected_actions_for_prs(GHInteractAction.PR_ADD_PENDING_LABEL, select_pull_requests_by_lookback(7)),
            ],
        ),
    ),
    reminds_those_within_pending=BackportCliCase(
        argv=["backport.py", "remind", "--lookback-days", "7"],
        gh_interaction=GHInteractionCase(
            # Has all the PRs
            repo=RepoCase(prs=select_pull_requests()),
            lookback_days=7,
            expected_prefetch_prs=[asdict(pr) for pr in select_pull_requests_by_lookback(7)],
            routes=[
                GHRoute(
                    path=f"/search/issues...merged...updated...",
                    method="GET",
                    # Prefetches only within 7 days (lookback)
                    response={"items": [asdict(pr) for pr in select_pull_requests_by_lookback(7)]},
                ),
                *build_gh_routes_labels("GET", select_pull_requests_by_lookback(7)),
            ],
            expected_order=[
                # Actions are dynamically created based on the needs_pending and needs_reminder flags
                *expected_actions_for_prs(GHInteractAction.ITER_PRS, select_pull_requests_by_lookback(7)),
            ],
        ),
    ),
    label_lookback_mode_merged=BackportCliCase(
        argv=["backport.py", "label", "--lookback-days", "7", "--lookback-mode", "merged"],
        gh_interaction=GHInteractionCase(
            repo=RepoCase(repo_labels=[], prs=select_pull_requests()),
            lookback_days=7,
            expected_prefetch_prs=[asdict(pr) for pr in select_pull_requests_by_lookback(7)],
            routes=[
                GHRoute(
                    path=f"/search/issues...merged...merged...",
                    method="GET",
                    response={"items": [asdict(pr) for pr in select_pull_requests_by_lookback(7)]},
                ),
                *build_gh_routes_labels("GET", select_pull_requests_by_lookback(7)),
                *build_gh_routes_labels("POST", select_pull_requests_by_lookback(7)),
                *build_gh_routes_repo(),
            ],
            expected_order=[
                *expected_actions_for_prs(GHInteractAction.ITER_PRS, select_pull_requests_by_lookback(7), lookback_mode="merged"),
                *expected_actions_for_repo(GHInteractAction.REPO_GET_LABELS),
                *expected_actions_for_repo(GHInteractAction.REPO_ADD_LABEL),
                *expected_actions_for_prs(GHInteractAction.PR_ADD_PENDING_LABEL, select_pull_requests_by_lookback(7)),
            ],
        ),
    ),
)
def test_backport_run(backport_mod, gh_mock, monkeypatch, case: BackportCliCase):
    """Basic sanity test of run_backport_cli."""
    case.gh_interaction.register(gh_mock)

    # Environment setup
    for k, v in case.env.items():
        monkeypatch.setenv(k, v)
    for k in case.delete_env:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(sys, "argv", case.argv)

    args = backport_mod.parse_args()
    backport_mod.configure(args)

    prefetched = backport_mod.prefetch_prs(args.pr_number, args.lookback_days, lookback_mode=args.lookback_mode)
    try:
        match args.command:
            case "label":
                result = backport_mod.run_label(prefetched, args.remove)
            case "remind":
                result = backport_mod.run_remind(prefetched, args.remove)
                for pr in prefetched:
                    if pr.get("needs_pending", False) is False:
                        case.gh_interaction.expected_order += expected_actions_for_prs(
                            GHInteractAction.PR_GET_COMMENTS, [case_by_number(pr.get("number"))]
                        )
                        if pr.get("needs_reminder", False):
                            case.gh_interaction.expected_order += expected_actions_for_prs(
                                GHInteractAction.PR_POST_REMINDER_COMMENT, [case_by_number(pr.get("number"))]
                            )
            case _:
                pytest.fail(f"Unknown command {args.command}")
    except Exception as e:
        pytest.fail(f"backport_run raised unexpected exception: {e}")

    assert result == 0
    gh_mock.assert_calls_in_order(*case.gh_interaction.expected_order)

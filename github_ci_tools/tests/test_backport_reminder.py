from dataclasses import asdict

from github_ci_tools.tests.resources.case_registry import (
    GHInteractAction,
    build_gh_routes_comments,
    case_by_number,
    expected_actions_for_prs,
    select_pull_requests,
)
from github_ci_tools.tests.resources.cases import (
    GHInteractionCase,
    PullRequestCase,
    RepoCase,
    cases,
)
from github_ci_tools.tests.utils import COMMENT_MARKER_BASE


@cases(
    pr_with_no_comments=case_by_number(201),
    pr_with_2_reminders=case_by_number(302),
    pr_with_120_old_comments=case_by_number(309),
    pr_with_really_old_reminder=case_by_number(303),
    pr_with_no_reminders=case_by_number(203),
)
def test_last_reminder_time(backport_mod, case: PullRequestCase):
    """Test determining the last reminder time from issue comments."""
    last_reminder = backport_mod.last_reminder_time([asdict(comment) for comment in case.comments], backport_mod.COMMENT_MARKER_BASE)
    expected_reminders = [comment for comment in case.comments if comment.is_reminder]
    if expected_reminders:
        expected_last_reminder = max(expected_reminders, key=lambda c: c.created_at_dt()).created_at_dt()
        assert last_reminder == expected_last_reminder
    else:
        assert last_reminder is None


@cases(
    from_single_pr_with_no_comments=GHInteractionCase(
        repo=RepoCase(
            prs=[case_by_number(201)],
        ),
        routes=[
            *build_gh_routes_comments("GET", [case_by_number(201)]),
        ],
        expected_order=[
            *expected_actions_for_prs(GHInteractAction.PR_GET_COMMENTS, [case_by_number(201)]),
        ],
    ),
    from_single_pr_with_120_old_comments=GHInteractionCase(
        repo=RepoCase(
            prs=[case_by_number(309)],
        ),
        routes=[
            *build_gh_routes_comments("GET", [case_by_number(309)]),
        ],
        expected_order=[
            *expected_actions_for_prs(GHInteractAction.PR_GET_COMMENTS, [case_by_number(309)]),
        ],
    ),
    fetch_from_all_prs=GHInteractionCase(
        repo=RepoCase(prs=select_pull_requests()),
        routes=[
            *build_gh_routes_comments("GET", select_pull_requests()),
        ],
        expected_order=[
            *expected_actions_for_prs(GHInteractAction.PR_GET_COMMENTS, select_pull_requests()),
        ],
    ),
)
def test_get_issue_comments(backport_mod, gh_mock, case: GHInteractionCase):
    """Test fetching issue comments with pagination."""
    case.register(gh_mock)
    for pr in case.repo.prs:
        total_comments = len(pr.comments)
        fetched_comments = backport_mod.get_issue_comments(pr.number)
        assert len(fetched_comments) == total_comments
        for comment in fetched_comments:
            assert comment in [asdict(c) for c in pr.comments]
    gh_mock.assert_calls_in_order(*case.expected_order)


@cases(
    pr_that_has_no_pending_label_does_not_get_commented=GHInteractionCase(
        repo=RepoCase(prs=[case_by_number(101)]),
        routes=[
            *build_gh_routes_comments("GET", [case_by_number(101)]),
        ],
    ),
    pr_has_pending_label_and_needs_reminder_gets_one=GHInteractionCase(
        repo=RepoCase(prs=[case_by_number(108)]),
        routes=[
            *build_gh_routes_comments("GET", [case_by_number(108)]),
            *build_gh_routes_comments("POST", [case_by_number(108)]),
        ],
    ),
    all_prs_have_pending_label_and_needs_reminder_get_one=GHInteractionCase(
        repo=RepoCase(prs=select_pull_requests(backport_pending_in_labels=True, needs_reminder=True)),
        routes=[
            *build_gh_routes_comments("GET", select_pull_requests(backport_pending_in_labels=True, needs_reminder=True)),
            *build_gh_routes_comments("POST", select_pull_requests(backport_pending_in_labels=True, needs_reminder=True)),
        ],
    ),
    all_prs_not_need_pending_and_has_reminder_does_not_get_one=GHInteractionCase(
        repo=RepoCase(prs=select_pull_requests(backport_pending_in_labels=False, needs_reminder=False)),
        routes=[
            *build_gh_routes_comments("GET", select_pull_requests(backport_pending_in_labels=False, needs_reminder=False)),
        ],
    ),
)
def test_remind_logic(backport_mod, gh_mock, case: GHInteractionCase):
    """Test of the exact logic as in run_label."""
    case.register(gh_mock)
    threshold = backport_mod.dt.datetime.now(backport_mod.dt.timezone.utc) - backport_mod.dt.timedelta(days=case.lookback_days)
    for pr in case.repo.prs:
        # Test of the exact logic as in run_remind.
        needs_reminder = backport_mod.pr_needs_reminder(backport_mod.PRInfo.from_dict(asdict(pr)), threshold)
        assert needs_reminder is pr.needs_reminder

        if needs_reminder:
            backport_mod.add_comment(pr.number, f"{COMMENT_MARKER_BASE}")

        if pr.needs_pending is False:
            case.expected_order += expected_actions_for_prs(GHInteractAction.PR_GET_COMMENTS, [case_by_number(pr.number)])
            if pr.needs_reminder:
                case.expected_order += expected_actions_for_prs(GHInteractAction.PR_POST_REMINDER_COMMENT, [case_by_number(pr.number)])

    gh_mock.assert_calls_in_order(*case.expected_order)

# rally-tracks

This repository contains the default track specifications for the Elasticsearch benchmarking tool [Rally](https://github.com/elastic/rally).

Tracks are used to describe benchmarks in Rally. For each track, the README.md file documents the data used, explains its parameters and provides an example document.

> [!NOTE]
> You can also [create your own track](https://esrally.readthedocs.io/en/latest/adding_tracks.html) to ensure your benchmarks will be as realistic as possible.

# Versioning Scheme

Refer to the official [Rally docs](https://esrally.readthedocs.io/en/stable/track.html#custom-track-repositories) for more details.

# How to Contribute

Contributions of new tracks should be compatible with the main version of Elasticsearch (i.e., pull requests should be submitted against the master branch). Feasibility of backporting to earlier Elasticsearch versions will be evaluated following submission.

> [!NOTE]
> See all details in the [contributor guidelines](https://github.com/elastic/rally/blob/master/CONTRIBUTING.md).

# Backporting changes

Backporting ensures that tracks are compatible not only with the latest `main` version of Elasticsearch, but also with previous versions. For this reason, backporting is an important part of the contribution process. Periodic reminders will be issued when a backport is pending.

To initiate backporting of a pull request, at least one `vX.Y` label must be applied.
- Apply all the labels that correspond to Elasticsearch minor versions expected to work with this PR, but select only from the available ones.

When adding a `vX.Y` label, the creation of a new PR is triggered unless there are merge conflicts. Its status is reported through a comment and in case it is successfully created, you get a link to  the PR opened against the target version branch. This new PR has a `backport` label and expects a review. When approved, it will be automatically merged.

## Merge conflicts
Merge conflicts need to be resolved manually. There are two ways to manually create a backport PR 

### Fork and cherry-pick
1. Fork the rally-tracks repository and clone it locally.
2. Pull and check out the intended version branch.
3. Create a new local branch from the selected version branch.
4. Cherry-pick the commit from the pull request to be backported.
5. Resolve any merge conflicts, commit the changes locally, and push to the fork.
6. Open a pull request against the target branch and manually add the backport label.
7. Request a review and proceed with merging.
8. Repeat this process for additional version branches as needed.

### Use backport tool (requires Node.js)
1. Refer to the [Backport tool](https://github.com/sorenlouv/backport?tab=readme-ov-file#backport-cli-tool) for installation instructions in the local rally-tracks directory. Ensure that a personal access token is configured in `~/.backport/config.json` with the required [repository access](https://github.com/sorenlouv/backport/blob/main/docs/config-file-options.md#global-config-backportconfigjson). Upon completion, the `backport` command should be available within the rally-tracks repository.
2. Navigate to the local `rally-tracks` repository and execute `backport --pr <merged_pr_number>`. This command initiates an interactive dialog for selecting branches to backport to. Only version branches with merge conflicts can be selected. After branch selection, the tool will indicate a directory (e.g., `Please fix the conflicts in /home/<user>/.backport/repositories/elastic/rally-tracks`) where conflicts must be resolved manually for each selected branch. If resolving multiple branches simultaneously is not feasible, repeat the procedure for each target version branch individually.
3. Once merge conflicts are resolved, re-execute `backport --pr <merged_pr_number>`. The process should now complete successfully, and pull requests will be opened against the target version branches, ready for review and merging.

## Backporting Notes
- CI is essential to this procedure. Whenever you commit something in a backport PR, check the test results.
- In case of conflicts, git blame is a wonderful tool to understand what changes need to be included in a version branch before backporting your PR. You can always check the history of the files you touch between the target backport branch and master version branch.
- Sometimes it is necessary to remove individual operations from a track that are not supported by earlier versions. This graceful fallback is a compromise to allow to run a subset of the track on older versions of Elasticsearch too.

## Finish line
For wrapping up ensure the following:
- Your merged PR has all the correct version labels.
- Every related backport PR has the `backport` label.
- Every related backport PR is merged to the correct version branches.

# License

There is no single license for this repository. Licenses are chosen per track. They are typically licensed under the same terms as the source data. See the README files of each track for more details.

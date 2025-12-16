# rally-tracks

This repository contains the default track specifications for the Elasticsearch benchmarking tool [Rally](https://github.com/elastic/rally).

Tracks are used to describe benchmarks in Rally. For each track, the README.md file documents the data used, explains its parameters and provides an example document.

> [!NOTE]
> It is also possible to create a [custom track](https://esrally.readthedocs.io/en/latest/adding_tracks.html) to ensure that benchmarks are as realistic as possible.

# Versioning Scheme

Refer to the official [Rally docs](https://esrally.readthedocs.io/en/stable/track.html#custom-track-repositories) for more details.

# How to Contribute

Contributions of new tracks should be compatible with the main version of Elasticsearch (i.e., pull requests should be submitted against the master branch). Feasibility of backporting to earlier Elasticsearch versions will be evaluated following submission.

> [!NOTE]
> For comprehensive instructions, refer to the [contributor guidelines](https://github.com/elastic/rally/blob/master/CONTRIBUTING.md).

# Backporting changes

Backporting ensures that tracks are compatible not only with the latest `main` version of Elasticsearch, but also with previous versions. For this reason, backporting is an important part of the contribution process. Periodic reminders will be issued when a backport is pending.

To initiate backporting of a pull request, at least one `vX.Y` label must be applied.
- Apply all labels corresponding to the current and previous Elasticsearch versions with which the pull request is expected to be compatible, selecting only from the available options.
- If the pull request introduces functionality dependent on future Elasticsearch versions, please wait until the relevant `X.Y` version branch is created. In such cases, it is recommended to retain the 'backport pending' label on the pull request to enable periodic notifications regarding the pending backport.

When a `vX.Y` label is added, a new pull request is automatically created, unless merge conflicts are detected. The status of this process is reported via a comment, and if successful, a link to the newly opened pull request targeting the specified version branch is provided. This pull request will include a `backport` label and will require a review. Upon approval, it will be merged automatically.

## Merge conflicts
Merge conflicts must be resolved manually. There are two primary methods for manually creating a backport pull request: 

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

> [!NOTE]
> In the event of conflicts, git blame is a useful tool for identifying changes that must be included in a version branch prior to backporting. The history of modified files can be compared between the target backport branch and the master branch.

## Backporting Notes
- Continuous Integration (CI) is integral to the backporting process. After each commit to a backport pull request, review the test results to ensure correctness.
- In the event of conflicts, git blame can be used to identify which changes need to be included in a version branch prior to backporting. The history of modified files can be compared between the target backport branch and the master branch.
- In some cases, it may be necessary to remove individual operations from a track that are not supported by earlier versions. This approach allows a subset of the track to run on older versions of Elasticsearch, providing a graceful fallback.

## Final steps
To complete the process, ensure the following:

- The merged pull request includes all relevant version labels.
- Each associated backport pull request is labeled with backport.
- Each backport pull request is merged into the appropriate version branch.

Finally, remove the `backport pending` label from your PR.

# License

There is no single license for this repository. Licenses are chosen per track. They are typically licensed under the same terms as the source data. See the README files of each track for more details.

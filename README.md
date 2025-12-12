# rally-tracks

This repository contains the default track specifications for the Elasticsearch benchmarking tool [Rally](https://github.com/elastic/rally).

Tracks are used to describe benchmarks in Rally. For each track, the README.md file documents the data used, explains its parameters and provides an example document.

> [!NOTE]
> You can also [create your own track](https://esrally.readthedocs.io/en/latest/adding_tracks.html) to ensure your benchmarks will be as realistic as possible.

# Versioning Scheme

Refer to the official [Rally docs](https://esrally.readthedocs.io/en/stable/track.html#custom-track-repositories) for more details.

# How to Contribute

If you want to contribute a track, please ensure that it works against the main version of Elasticsearch (i.e. submit PRs against the master branch). We can then check whether it's feasible to backport the track to earlier Elasticsearch versions.

> [!NOTE]
> See all details in the [contributor guidelines](https://github.com/elastic/rally/blob/master/CONTRIBUTING.md).

# Backporting changes

Backporting ensures that tracks do not work only for the latest `main` version of Elasticsearch but also for older versions, so it is important. As part of contributing to this repository, a reminder will periodically notify you that backport is pending.

In order to backport your PR, at least one `vX.Y` label has to be added. 
- Please supply all the labels that correspond to both current and past elasticsearch versions you expect this PR to work with, but choose only from all the available ones. 
- If the PR being merged is using functionality from future Elasticsearch versions, please wait for the creation of new Elasticsearch `vX.Y` version branch. In such case, it would be useful if you kept the 'backport pending' label attached to the PR, so the backport reminder can periodically notify you.

When adding a `vX.Y` label, the creation of a new PR is triggered unless there are merge conflicts. Its status is reported through a comment and in case it is successfully created, you get a link to  the PR opened against the target version branch. This new PR has a `backport` label and expects a review. When approved, it will be automatically merged.

## Merge conflicts
Merge conflicts need to be resolved manually. There are two ways to manually create a backport PR 

## Fork and cherry-pick
1. Create a rally-tracks fork, and clone it locally.
2. Pull and checkout to the intended version branch. 
3. Create a new local branch from this version branch.
4. Cherry-pick the commit from the PR that will be backported.
5. Resolve merge conflicts, commit locally and push to fork.
6. Open a PR against the target branch, add `backport` label manually.
7. Request a review and merge.
8. Repeat for other version branches. 

## Use backport tool (requires node)
1. Go to the [Backport tool](https://github.com/sorenlouv/backport?tab=readme-ov-file#backport-cli-tool) documentation and follow the guidelines to install it in your local `rally-tracks` directory. Note that you have to add your personal access secret token locally in `~/.backport/config.json` with the [specified](https://github.com/sorenlouv/backport/blob/main/docs/config-file-options.md#global-config-backportconfigjson) repository access. At the end of this step, you should be able to execute `backport` command inside rally-tracks repo.
2. cd in your local `rally-tracks` repository and execute `backport --pr <merged_pr_number>`. This will open an interactive dialog where you are required to selected branches to backport to. You can only select the version branches that have merge conflicts. After selecting the branches, backport tool will mention some directory in a message `Please fix the conflicts in /home/<user>/.backport/repositories/elastic/rally-tracks` and you will have to go and resolve those conflicts manually for all of the selected branches. If it is not easy to tackle multiple branches in a single sweep, repeat this procedure for each target version branch separately.
3. After resolving the merge conflicts you can execute `backport --pr <merged_pr_number>` which this time it will be successful. PRs will be opened against the target version branches and they will be ready for approval and merge.

## Backporting Notes
- CI is essential to this procedure. Whenever you commit something in a backport PR, check the test results.
- In case of conflicts, git blame is a wonderful tool to understand what changes need to be included in a version branch before backporting your PR. You can always check the history of the files you touch between the target backport branch and master version branch.
- Sometimes it is necessary to remove individual operations from a track that are not supported by earlier versions. This graceful fallback is a compromise to allow to run a subset of the track on older versions of Elasticsearch too.

## Finish line
For wrapping up ensure the following:
- Your merged PR has all the correct version labels.
- Every related backport PR has the `backport` label.
- Every related backport PR is merged to the correct version branches.

Finally, remove the `backport pending` label from your PR.

# License

There is no single license for this repository. Licenses are chosen per track. They are typically licensed under the same terms as the source data. See the README files of each track for more details.

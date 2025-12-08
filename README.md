rally-tracks
------------

This repository contains the default track specifications for the Elasticsearch benchmarking tool [Rally](https://github.com/elastic/rally).

Tracks are used to describe benchmarks in Rally. For each track, the README.md file documents the data used, explains its parameters and provides an example document.

You can also [create your own track](https://esrally.readthedocs.io/en/latest/adding_tracks.html) to ensure your benchmarks will be as realistic as possible.

Versioning Scheme
-----------------

Refer to the official [Rally docs](https://esrally.readthedocs.io/en/stable/track.html#custom-track-repositories) for more details.

How to Contribute
-----------------

If you want to contribute a track, please ensure that it works against the main version of Elasticsearch (i.e. submit PRs against the master branch). We can then check whether it's feasible to backport the track to earlier Elasticsearch versions.

See all details in the [contributor guidelines](https://github.com/elastic/rally/blob/master/CONTRIBUTING.md).

Backporting changes
-------------------

As part of contributing to this repository, a reminder will periodically notify you that backport is pending. Backporting ensures that tracks do not work only for the latest `main` version of Elasticsearch but also for older versions, so it is important.

In order to backport your PR, at least one `vX.Y` label has to be added. 
- Please supply all the labels that correspond to both current and past elasticsearch versions you expect this PR to work with, but choose only from all the available ones. 
- If the PR you are merging is using functionality from future Elasticsearch versions, please wait for the feature freeze action of Elasticsearch to create the new label in this repository and then add it. In such case, it would be useful if you kept the 'backport pending' label attached to the PR, so the backport reminder can periodically notify you.

Every `vX.Y` label is triggering a new PR unless there are merge conflicts. This is the backport action, the status of which is reported through a comment.
- In case of successful backport action, you get a link to the PR opened against the target version branch, in which you are expected to review the changes to this version branch and when approved, it will be automatically merged.
- In case of merge conflicts a series of manual actions are necessary:

1. Go to the [Backport tool](https://github.com/sorenlouv/backport?tab=readme-ov-file#backport-cli-tool) documentation and follow the guidelines to install it in your local `rally-tracks` directory. Note that you have to add your personal access secret token locally in `~/.backport/config.json` with the [specified](https://github.com/sorenlouv/backport/blob/main/docs/config-file-options.md#global-config-backportconfigjson) repository access. At the end of this step, you should be able to execute `backport` command inside rally-tracks repo.
2. cd in your local `rally-tracks` repository and execute `backport --pr <merged_and_conflicting_pr_number>`. This will open an interactive dialog where you are required to selected branches to backport to. You can only select the version branches that have merge conflicts. After selecting the branches, backport tool will mention a directory in a message `Please fix the conflicts in /home/<user>/.backport/repositories/elastic/rally-tracks` and you will have to go and resolve those conflicts manually for all of the selected branches. If it is not easy to tackle multiple branches in a single sweep, repeat this procedure for each target version branch separately.
3. After resolving the merge conflicts you can execute `backport --pr` again and this time it will be successful. PRs will be opened against the target version branches and they will be ready for approval and merge.


### Backporting Notes
- In case of conflicts, git blame is a wonderful tool to understand what changes need to be included in a version branch before backporting your PR. You can always check the history of the files you touch between the target backport branch and the next version branch (or master). Also, be mindful of the files that are not changed, but refer to the changed files.
- Sometimes it is necessary to remove individual operations from a track that are not supported by earlier versions. This graceful fallback is a compromise to allow to run a subset of the track on older versions of Elasticsearch too. If this is necessary then it's best to do these changes in a separate commit. 
- You can backport individual commits to even earlier versions if necessary by cherry-picking them into the desired version branches.


License
-------

There is no single license for this repository. Licenses are chosen per track. They are typically licensed under the same terms as the source data. See the README files of each track for more details.

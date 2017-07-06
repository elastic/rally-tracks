rally-tracks
------------

This repository contains the default track specifications for the Elasticsearch benchmarking tool [Rally](https://github.com/elastic/rally).

Tracks are used to describe benchmarks in Rally.

You should not need to use this repository directly, except if you want to look under the hood or create your own tracks. We have created a [tutorial on how to create your own tracks](https://esrally.readthedocs.io/en/latest/adding_tracks.html).

Versioning Scheme
-----------------

From time to time, setting and mapping formats change in Elasticsearch. As we want to be able to support multiple versions of Elasticsearch, we also need to version track specifications. Therefore, this repository contains multiple branches. The following examples should give you an idea how the versioning scheme works:

* master: tracks on this branch are compatible with the latest development version of Elasticsearch
* 5.0.0-alpha2: compatible with the released version 5.0.0-alpha2.
* 2: compatible with all Elasticsearch releases with the major release number 2 (e.g. 2.1, 2.2, 2.2.1)
* 1.7: compatible with all Elasticsearch releases with the major release number 1 and minor release number 7 (e.g. 1.7.0, 1.7.1, 1.7.2)

As you can see, branches can match exact release numbers but Rally is also lenient in case settings mapping formats did not change for a few releases. Rally will try to match in the following order:

1. major.minor.patch-extension_label (e.g. 5.0.0-alpha5)
2. major.minor.patch (e.g. 2.3.1)
3. major.minor (e.g. 2.3)
4. major (e.g. 2)

Apart from that, the master branch is always considered to be compatible with the Elasticsearch master branch.

To specify the version to check against, add `--distribution-version` when running Rally. It it is not specified, Rally assumes that you want to benchmark against the Elasticsearch master version. 

Example: If you want to benchmark Elasticsearch 5.0.0, run the following command:

```
esrally --distribution-version=5.0.0
```

How to Contribute
-----------------

If you want to contribute a track, please ensure that it works against the master version of Elasticsearch (i.e. submit PRs against the master branch). We can then check whether it's feasible to backport the track to earlier Elasticsearch versions.
 
See all details in the [contributor guidelines](https://github.com/elastic/rally/blob/master/CONTRIBUTING.md).

Backporting changes
-------------------

If you are a contributor with direct commit access to this repository then please backport your changes. This ensures that tracks do not work only for the latest `master` version of Elasticsearch but also for older versions. Apply backports with cherr-picks. Below you can find a walkthrough:

Assume we've pushed commit `a7e0937` to master and want to backport it. This is a change to the `noaa` track. Let's check what branches are available for backporting:

```
daniel@io:tracks/default ‹master›$ git branch -r
  origin/1
  origin/2
  origin/5
  origin/HEAD -> origin/master
  origin/master
```

We'll go backwards starting from branch `5`, then branch `2` and finally branch `1`. After applying a change, we will test whether the track works as is for an older version of Elasticsearch.

```
git checkout 5
git cherry-pick a7e0937

# test the change now with an Elasticsearch 5.x distribution
esrally --track=noaa --distribution-version=5.4.3 --test-mode

# push the change
git push origin 5
```

This particular track uses features that are only available in Elasticsearch 5 and later so we will stop here but the process continues until we've reached the earliest branch. 

Sometimes it is necessary to remove individual operations from a track that are not supported by earlier versions. This graceful fallback is a compromise to allow to run a subset of the track on older versions of Elasticsearch too. If this is necessary then it's best to do these changes in a separate commit. Also, don't forget to cherry-pick this separate commit too to even earlier versions if necessary.  

 
License
-------
 
There is no single license for this repository. Licenses are chosen per track. They are typically licensed under the same terms as the source data. See the README files of each track for more details.
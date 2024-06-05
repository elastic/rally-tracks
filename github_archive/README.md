# GitHub Archive Track

This is a Rally track using data from the [GH Archive](https://www.gharchive.org/) project for events ranging from `2021-10-01T00:00:00Z` to `2021-10-07T23:59:58Z`. All event data is indexed in its raw form as it exists in the source. When using the `data_stream` ingest mode, the `created_at` field is copied to `@timestamp` using the `copy_to` index mapping parameter.

## Example Document

<details><summary>PullRequestEvent</summary>

```json
{
    "id": "18297969542",
    "type": "PullRequestEvent",
    "actor": {
      "id": 7461306,
      "login": "jtibshirani",
      "display_login": "jtibshirani",
      "gravatar_id": "",
      "url": "https://api.github.com/users/jtibshirani",
      "avatar_url": "https://avatars.githubusercontent.com/u/7461306?"
    },
    "repo": {
      "id": 507775,
      "name": "elastic/elasticsearch",
      "url": "https://api.github.com/repos/elastic/elasticsearch"
    },
    "payload": {
      "action": "opened",
      "number": 78724,
      "pull_request": {
        "url": "https://api.github.com/repos/elastic/elasticsearch/pulls/78724",
        "id": 750430215,
        "node_id": "PR_kwDOAAe_f84suqgH",
        "html_url": "https://github.com/elastic/elasticsearch/pull/78724",
        "diff_url": "https://github.com/elastic/elasticsearch/pull/78724.diff",
        "patch_url": "https://github.com/elastic/elasticsearch/pull/78724.patch",
        "issue_url": "https://api.github.com/repos/elastic/elasticsearch/issues/78724",
        "number": 78724,
        "state": "open",
        "locked": false,
        "title": "Load knn vectors format with mmapfs",
        "user": {
          "login": "jtibshirani",
          "id": 7461306,
          "node_id": "MDQ6VXNlcjc0NjEzMDY=",
          "avatar_url": "https://avatars.githubusercontent.com/u/7461306?v=4",
          "gravatar_id": "",
          "url": "https://api.github.com/users/jtibshirani",
          "html_url": "https://github.com/jtibshirani",
          "followers_url": "https://api.github.com/users/jtibshirani/followers",
          "following_url": "https://api.github.com/users/jtibshirani/following{/other_user}",
          "gists_url": "https://api.github.com/users/jtibshirani/gists{/gist_id}",
          "starred_url": "https://api.github.com/users/jtibshirani/starred{/owner}{/repo}",
          "subscriptions_url": "https://api.github.com/users/jtibshirani/subscriptions",
          "organizations_url": "https://api.github.com/users/jtibshirani/orgs",
          "repos_url": "https://api.github.com/users/jtibshirani/repos",
          "events_url": "https://api.github.com/users/jtibshirani/events{/privacy}",
          "received_events_url": "https://api.github.com/users/jtibshirani/received_events",
          "type": "User",
          "site_admin": false
        },
        "body": "Before the format used niofs. The current knn vectors implementation is based on\r\nthe HNSW algorithm, which is designed for the case where the graph and vectors\r\nare be held in memory. Switching to mmapfs from niofs made a big difference in\r\nANN benchmarks, speeding up some searches over 3x.\r\n\r\nRelates to #78473.",
        "created_at": "2021-10-05T22:34:15Z",
        "updated_at": "2021-10-05T22:34:15Z",
        "closed_at": null,
        "merged_at": null,
        "merge_commit_sha": null,
        "assignee": null,
        "assignees": [],
        "requested_reviewers": [],
        "requested_teams": [],
        "labels": [
          {
            "id": 146832564,
            "node_id": "MDU6TGFiZWwxNDY4MzI1NjQ=",
            "url": "https://api.github.com/repos/elastic/elasticsearch/labels/:Search/Search",
            "name": ":Search/Search",
            "color": "0e8a16",
            "default": false,
            "description": "Search-related issues that do not fall into other categories"
          },
          {
            "id": 1194435738,
            "node_id": "MDU6TGFiZWwxMTk0NDM1NzM4",
            "url": "https://api.github.com/repos/elastic/elasticsearch/labels/v8.0.0",
            "name": "v8.0.0",
            "color": "dddddd",
            "default": false,
            "description": ""
          }
        ],
        "milestone": null,
        "draft": true,
        "commits_url": "https://api.github.com/repos/elastic/elasticsearch/pulls/78724/commits",
        "review_comments_url": "https://api.github.com/repos/elastic/elasticsearch/pulls/78724/comments",
        "review_comment_url": "https://api.github.com/repos/elastic/elasticsearch/pulls/comments{/number}",
        "comments_url": "https://api.github.com/repos/elastic/elasticsearch/issues/78724/comments",
        "statuses_url": "https://api.github.com/repos/elastic/elasticsearch/statuses/f1fd5119702f71238c2dfc422296b8ef1f7f6740",
        "head": {
          "label": "jtibshirani:vectors-format",
          "ref": "vectors-format",
          "sha": "f1fd5119702f71238c2dfc422296b8ef1f7f6740",
          "user": {
            "login": "jtibshirani",
            "id": 7461306,
            "node_id": "MDQ6VXNlcjc0NjEzMDY=",
            "avatar_url": "https://avatars.githubusercontent.com/u/7461306?v=4",
            "gravatar_id": "",
            "url": "https://api.github.com/users/jtibshirani",
            "html_url": "https://github.com/jtibshirani",
            "followers_url": "https://api.github.com/users/jtibshirani/followers",
            "following_url": "https://api.github.com/users/jtibshirani/following{/other_user}",
            "gists_url": "https://api.github.com/users/jtibshirani/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/jtibshirani/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/jtibshirani/subscriptions",
            "organizations_url": "https://api.github.com/users/jtibshirani/orgs",
            "repos_url": "https://api.github.com/users/jtibshirani/repos",
            "events_url": "https://api.github.com/users/jtibshirani/events{/privacy}",
            "received_events_url": "https://api.github.com/users/jtibshirani/received_events",
            "type": "User",
            "site_admin": false
          },
          "repo": {
            "id": 129949784,
            "node_id": "MDEwOlJlcG9zaXRvcnkxMjk5NDk3ODQ=",
            "name": "elasticsearch",
            "full_name": "jtibshirani/elasticsearch",
            "private": false,
            "owner": {
              "login": "jtibshirani",
              "id": 7461306,
              "node_id": "MDQ6VXNlcjc0NjEzMDY=",
              "avatar_url": "https://avatars.githubusercontent.com/u/7461306?v=4",
              "gravatar_id": "",
              "url": "https://api.github.com/users/jtibshirani",
              "html_url": "https://github.com/jtibshirani",
              "followers_url": "https://api.github.com/users/jtibshirani/followers",
              "following_url": "https://api.github.com/users/jtibshirani/following{/other_user}",
              "gists_url": "https://api.github.com/users/jtibshirani/gists{/gist_id}",
              "starred_url": "https://api.github.com/users/jtibshirani/starred{/owner}{/repo}",
              "subscriptions_url": "https://api.github.com/users/jtibshirani/subscriptions",
              "organizations_url": "https://api.github.com/users/jtibshirani/orgs",
              "repos_url": "https://api.github.com/users/jtibshirani/repos",
              "events_url": "https://api.github.com/users/jtibshirani/events{/privacy}",
              "received_events_url": "https://api.github.com/users/jtibshirani/received_events",
              "type": "User",
              "site_admin": false
            },
            "html_url": "https://github.com/jtibshirani/elasticsearch",
            "description": "Open Source, Distributed, RESTful Search Engine",
            "fork": true,
            "url": "https://api.github.com/repos/jtibshirani/elasticsearch",
            "forks_url": "https://api.github.com/repos/jtibshirani/elasticsearch/forks",
            "keys_url": "https://api.github.com/repos/jtibshirani/elasticsearch/keys{/key_id}",
            "collaborators_url": "https://api.github.com/repos/jtibshirani/elasticsearch/collaborators{/collaborator}",
            "teams_url": "https://api.github.com/repos/jtibshirani/elasticsearch/teams",
            "hooks_url": "https://api.github.com/repos/jtibshirani/elasticsearch/hooks",
            "issue_events_url": "https://api.github.com/repos/jtibshirani/elasticsearch/issues/events{/number}",
            "events_url": "https://api.github.com/repos/jtibshirani/elasticsearch/events",
            "assignees_url": "https://api.github.com/repos/jtibshirani/elasticsearch/assignees{/user}",
            "branches_url": "https://api.github.com/repos/jtibshirani/elasticsearch/branches{/branch}",
            "tags_url": "https://api.github.com/repos/jtibshirani/elasticsearch/tags",
            "blobs_url": "https://api.github.com/repos/jtibshirani/elasticsearch/git/blobs{/sha}",
            "git_tags_url": "https://api.github.com/repos/jtibshirani/elasticsearch/git/tags{/sha}",
            "git_refs_url": "https://api.github.com/repos/jtibshirani/elasticsearch/git/refs{/sha}",
            "trees_url": "https://api.github.com/repos/jtibshirani/elasticsearch/git/trees{/sha}",
            "statuses_url": "https://api.github.com/repos/jtibshirani/elasticsearch/statuses/{sha}",
            "languages_url": "https://api.github.com/repos/jtibshirani/elasticsearch/languages",
            "stargazers_url": "https://api.github.com/repos/jtibshirani/elasticsearch/stargazers",
            "contributors_url": "https://api.github.com/repos/jtibshirani/elasticsearch/contributors",
            "subscribers_url": "https://api.github.com/repos/jtibshirani/elasticsearch/subscribers",
            "subscription_url": "https://api.github.com/repos/jtibshirani/elasticsearch/subscription",
            "commits_url": "https://api.github.com/repos/jtibshirani/elasticsearch/commits{/sha}",
            "git_commits_url": "https://api.github.com/repos/jtibshirani/elasticsearch/git/commits{/sha}",
            "comments_url": "https://api.github.com/repos/jtibshirani/elasticsearch/comments{/number}",
            "issue_comment_url": "https://api.github.com/repos/jtibshirani/elasticsearch/issues/comments{/number}",
            "contents_url": "https://api.github.com/repos/jtibshirani/elasticsearch/contents/{+path}",
            "compare_url": "https://api.github.com/repos/jtibshirani/elasticsearch/compare/{base}...{head}",
            "merges_url": "https://api.github.com/repos/jtibshirani/elasticsearch/merges",
            "archive_url": "https://api.github.com/repos/jtibshirani/elasticsearch/{archive_format}{/ref}",
            "downloads_url": "https://api.github.com/repos/jtibshirani/elasticsearch/downloads",
            "issues_url": "https://api.github.com/repos/jtibshirani/elasticsearch/issues{/number}",
            "pulls_url": "https://api.github.com/repos/jtibshirani/elasticsearch/pulls{/number}",
            "milestones_url": "https://api.github.com/repos/jtibshirani/elasticsearch/milestones{/number}",
            "notifications_url": "https://api.github.com/repos/jtibshirani/elasticsearch/notifications{?since,all,participating}",
            "labels_url": "https://api.github.com/repos/jtibshirani/elasticsearch/labels{/name}",
            "releases_url": "https://api.github.com/repos/jtibshirani/elasticsearch/releases{/id}",
            "deployments_url": "https://api.github.com/repos/jtibshirani/elasticsearch/deployments",
            "created_at": "2018-04-17T18:41:01Z",
            "updated_at": "2021-05-20T20:29:02Z",
            "pushed_at": "2021-10-05T22:33:11Z",
            "git_url": "git://github.com/jtibshirani/elasticsearch.git",
            "ssh_url": "git@github.com:jtibshirani/elasticsearch.git",
            "clone_url": "https://github.com/jtibshirani/elasticsearch.git",
            "svn_url": "https://github.com/jtibshirani/elasticsearch",
            "homepage": "https://www.elastic.co/products/elasticsearch",
            "size": 700905,
            "stargazers_count": 0,
            "watchers_count": 0,
            "language": "Java",
            "has_issues": false,
            "has_projects": true,
            "has_downloads": true,
            "has_wiki": false,
            "has_pages": false,
            "forks_count": 0,
            "mirror_url": null,
            "archived": false,
            "disabled": false,
            "open_issues_count": 2,
            "license": {
              "key": "other",
              "name": "Other",
              "spdx_id": "NOASSERTION",
              "url": null,
              "node_id": "MDc6TGljZW5zZTA="
            },
            "allow_forking": true,
            "visibility": "public",
            "forks": 0,
            "open_issues": 2,
            "watchers": 0,
            "default_branch": "master"
          }
        },
        "base": {
          "label": "elastic:master",
          "ref": "master",
          "sha": "abe0c06afd92ba89a3c110d4fbec6a85ec06c377",
          "user": {
            "login": "elastic",
            "id": 6764390,
            "node_id": "MDEyOk9yZ2FuaXphdGlvbjY3NjQzOTA=",
            "avatar_url": "https://avatars.githubusercontent.com/u/6764390?v=4",
            "gravatar_id": "",
            "url": "https://api.github.com/users/elastic",
            "html_url": "https://github.com/elastic",
            "followers_url": "https://api.github.com/users/elastic/followers",
            "following_url": "https://api.github.com/users/elastic/following{/other_user}",
            "gists_url": "https://api.github.com/users/elastic/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/elastic/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/elastic/subscriptions",
            "organizations_url": "https://api.github.com/users/elastic/orgs",
            "repos_url": "https://api.github.com/users/elastic/repos",
            "events_url": "https://api.github.com/users/elastic/events{/privacy}",
            "received_events_url": "https://api.github.com/users/elastic/received_events",
            "type": "Organization",
            "site_admin": false
          },
          "repo": {
            "id": 507775,
            "node_id": "MDEwOlJlcG9zaXRvcnk1MDc3NzU=",
            "name": "elasticsearch",
            "full_name": "elastic/elasticsearch",
            "private": false,
            "owner": {
              "login": "elastic",
              "id": 6764390,
              "node_id": "MDEyOk9yZ2FuaXphdGlvbjY3NjQzOTA=",
              "avatar_url": "https://avatars.githubusercontent.com/u/6764390?v=4",
              "gravatar_id": "",
              "url": "https://api.github.com/users/elastic",
              "html_url": "https://github.com/elastic",
              "followers_url": "https://api.github.com/users/elastic/followers",
              "following_url": "https://api.github.com/users/elastic/following{/other_user}",
              "gists_url": "https://api.github.com/users/elastic/gists{/gist_id}",
              "starred_url": "https://api.github.com/users/elastic/starred{/owner}{/repo}",
              "subscriptions_url": "https://api.github.com/users/elastic/subscriptions",
              "organizations_url": "https://api.github.com/users/elastic/orgs",
              "repos_url": "https://api.github.com/users/elastic/repos",
              "events_url": "https://api.github.com/users/elastic/events{/privacy}",
              "received_events_url": "https://api.github.com/users/elastic/received_events",
              "type": "Organization",
              "site_admin": false
            },
            "html_url": "https://github.com/elastic/elasticsearch",
            "description": "Free and Open, Distributed, RESTful Search Engine",
            "fork": false,
            "url": "https://api.github.com/repos/elastic/elasticsearch",
            "forks_url": "https://api.github.com/repos/elastic/elasticsearch/forks",
            "keys_url": "https://api.github.com/repos/elastic/elasticsearch/keys{/key_id}",
            "collaborators_url": "https://api.github.com/repos/elastic/elasticsearch/collaborators{/collaborator}",
            "teams_url": "https://api.github.com/repos/elastic/elasticsearch/teams",
            "hooks_url": "https://api.github.com/repos/elastic/elasticsearch/hooks",
            "issue_events_url": "https://api.github.com/repos/elastic/elasticsearch/issues/events{/number}",
            "events_url": "https://api.github.com/repos/elastic/elasticsearch/events",
            "assignees_url": "https://api.github.com/repos/elastic/elasticsearch/assignees{/user}",
            "branches_url": "https://api.github.com/repos/elastic/elasticsearch/branches{/branch}",
            "tags_url": "https://api.github.com/repos/elastic/elasticsearch/tags",
            "blobs_url": "https://api.github.com/repos/elastic/elasticsearch/git/blobs{/sha}",
            "git_tags_url": "https://api.github.com/repos/elastic/elasticsearch/git/tags{/sha}",
            "git_refs_url": "https://api.github.com/repos/elastic/elasticsearch/git/refs{/sha}",
            "trees_url": "https://api.github.com/repos/elastic/elasticsearch/git/trees{/sha}",
            "statuses_url": "https://api.github.com/repos/elastic/elasticsearch/statuses/{sha}",
            "languages_url": "https://api.github.com/repos/elastic/elasticsearch/languages",
            "stargazers_url": "https://api.github.com/repos/elastic/elasticsearch/stargazers",
            "contributors_url": "https://api.github.com/repos/elastic/elasticsearch/contributors",
            "subscribers_url": "https://api.github.com/repos/elastic/elasticsearch/subscribers",
            "subscription_url": "https://api.github.com/repos/elastic/elasticsearch/subscription",
            "commits_url": "https://api.github.com/repos/elastic/elasticsearch/commits{/sha}",
            "git_commits_url": "https://api.github.com/repos/elastic/elasticsearch/git/commits{/sha}",
            "comments_url": "https://api.github.com/repos/elastic/elasticsearch/comments{/number}",
            "issue_comment_url": "https://api.github.com/repos/elastic/elasticsearch/issues/comments{/number}",
            "contents_url": "https://api.github.com/repos/elastic/elasticsearch/contents/{+path}",
            "compare_url": "https://api.github.com/repos/elastic/elasticsearch/compare/{base}...{head}",
            "merges_url": "https://api.github.com/repos/elastic/elasticsearch/merges",
            "archive_url": "https://api.github.com/repos/elastic/elasticsearch/{archive_format}{/ref}",
            "downloads_url": "https://api.github.com/repos/elastic/elasticsearch/downloads",
            "issues_url": "https://api.github.com/repos/elastic/elasticsearch/issues{/number}",
            "pulls_url": "https://api.github.com/repos/elastic/elasticsearch/pulls{/number}",
            "milestones_url": "https://api.github.com/repos/elastic/elasticsearch/milestones{/number}",
            "notifications_url": "https://api.github.com/repos/elastic/elasticsearch/notifications{?since,all,participating}",
            "labels_url": "https://api.github.com/repos/elastic/elasticsearch/labels{/name}",
            "releases_url": "https://api.github.com/repos/elastic/elasticsearch/releases{/id}",
            "deployments_url": "https://api.github.com/repos/elastic/elasticsearch/deployments",
            "created_at": "2010-02-08T13:20:56Z",
            "updated_at": "2021-10-05T21:26:32Z",
            "pushed_at": "2021-10-05T22:22:27Z",
            "git_url": "git://github.com/elastic/elasticsearch.git",
            "ssh_url": "git@github.com:elastic/elasticsearch.git",
            "clone_url": "https://github.com/elastic/elasticsearch.git",
            "svn_url": "https://github.com/elastic/elasticsearch",
            "homepage": "https://www.elastic.co/products/elasticsearch",
            "size": 879825,
            "stargazers_count": 56690,
            "watchers_count": 56690,
            "language": "Java",
            "has_issues": true,
            "has_projects": true,
            "has_downloads": true,
            "has_wiki": false,
            "has_pages": false,
            "forks_count": 20670,
            "mirror_url": null,
            "archived": false,
            "disabled": false,
            "open_issues_count": 3546,
            "license": {
              "key": "other",
              "name": "Other",
              "spdx_id": "NOASSERTION",
              "url": null,
              "node_id": "MDc6TGljZW5zZTA="
            },
            "allow_forking": true,
            "visibility": "public",
            "forks": 20670,
            "open_issues": 3546,
            "watchers": 56690,
            "default_branch": "master"
          }
        },
        "_links": {
          "self": {
            "href": "https://api.github.com/repos/elastic/elasticsearch/pulls/78724"
          },
          "html": {
            "href": "https://github.com/elastic/elasticsearch/pull/78724"
          },
          "issue": {
            "href": "https://api.github.com/repos/elastic/elasticsearch/issues/78724"
          },
          "comments": {
            "href": "https://api.github.com/repos/elastic/elasticsearch/issues/78724/comments"
          },
          "review_comments": {
            "href": "https://api.github.com/repos/elastic/elasticsearch/pulls/78724/comments"
          },
          "review_comment": {
            "href": "https://api.github.com/repos/elastic/elasticsearch/pulls/comments{/number}"
          },
          "commits": {
            "href": "https://api.github.com/repos/elastic/elasticsearch/pulls/78724/commits"
          },
          "statuses": {
            "href": "https://api.github.com/repos/elastic/elasticsearch/statuses/f1fd5119702f71238c2dfc422296b8ef1f7f6740"
          }
        },
        "author_association": "MEMBER",
        "auto_merge": null,
        "active_lock_reason": null,
        "merged": false,
        "mergeable": null,
        "rebaseable": null,
        "mergeable_state": "draft",
        "merged_by": null,
        "comments": 0,
        "review_comments": 0,
        "maintainer_can_modify": true,
        "commits": 1,
        "additions": 2,
        "deletions": 2,
        "changed_files": 1
      }
    },
    "public": true,
    "created_at": "2021-10-05T22:34:15Z",
    "org": {
      "id": 6764390,
      "login": "elastic",
      "gravatar_id": "",
      "url": "https://api.github.com/orgs/elastic",
      "avatar_url": "https://avatars.githubusercontent.com/u/6764390?"
    }
  }
  ```
</details>

## Track Parameters

Track parameters are specified using `--track-params`; e.g., `--track-params="bulk_size:1000,ingest_percentage:75"`

| Parameter | Default | Description |
| --- | --- | --- |
| `bulk_size` | `5000` | The number of batched documents per bulk request. |
| `bulk_indexing_clients` | `8` | Number of clients issuing bulk indexing requests |
| `cluster_health` | `green` | Minimum cluster status required before proceeding to bulk indexing. Valid values are `green`, `yellow`, and `red`. |
| `codec` | `default` | The index compression codec to use. Use `best_compression` for higher compression at the cost of CPU. |
| `conflicts` | unset | The type of conflicts to simulate during bulk indexing. Valid values are `sequential` and `random`.  See the `conflicts` property in the [bulk operation documentation](https://esrally.readthedocs.io/en/latest/track.html#bulk) for details. This parameter is incompatible with data stream indexing. |
| `conflict_probability` | `25` | A number between `0` and `100` defining the percentage of documents to replace on concflict. See the `conflict-probability` property in the [bulk operation documentation](https://esrally.readthedocs.io/en/latest/track.html#bulk) for details. This parameter is incompatible with data stream indexing. |
| `on_conflict` | `index` | Valid values are `index` and `update`. Specifies if Rally should perform a new indexing action or update existing documents on id conflicts. See the `on-conflict` property in the [bulk operation documentation](https://esrally.readthedocs.io/en/latest/track.html#bulk) for details. This parameter is incompatible with data stream indexing. |
| `data_stream` | `false` | By default, the track ingests to a standard index. A value of `true` ingests to a data stream.
| `ingest_percentage` | `100` | A number between 0 and 100 representing how much of the document corpus should be indexed. |
| `max_page_search_size` | `500` | Defines the initial composite aggregation page size for each checkpoint when creating transforms. |
| `number_of_shards` | `1` | Set the number of index primary shards. |
| `number_of_replicas` | `0` | Set the number of replica shards per primary. |
| `refresh_interval` | unest | Set the index refresh interval. |
| `runtime_bulk_indexing_clients` | `8` | The number of bulk indexing clients during parallel indexing and search tasks. |
| `runtime_bulk_size` | `100` | The number of batched documents per bulk request during parallel indexing and search tasks. |
| `runtime_search_clients` | `8` | The number of search clients during parallel indexing and search tasks. |

## Tags

Setup tasks for deleting/creating indices and data streams, deleting/creating templates, and waiting for cluster health are tagged with `setup`. These tasks can be excluded with `--exclude-tasks="tag:setup"`.

## Track Info

### Standard index

```shell
Showing details for track [github_archive]:

* Description: GitHub timeline from gharchive.org
* Documents: 21,435,282
* Compressed Size: 7.6 GB
* Uncompressed Size: 107.3 GB

======================
Challenge [index-only]
======================

Index the document corpus

Schedule:
----------

1. delete-index
2. delete-data-stream-gharchive
3. create-index
4. wait-for-cluster-health-status-green
5. index (8 clients)

========================================
Challenge [parallel-indexing-and-search]
========================================

Index the document corpus, then perform parallel indexing and search operations

Schedule:
----------

1. delete-index
2. delete-data-stream-gharchive
3. create-index
4. wait-for-cluster-health-status-green
5. index_corpora1 (8 clients)
6. refresh-after-index
7. add_filter_alias
8. 3 parallel tasks (16 clients):
	8.1 index_corpora2_parallel_task (8 clients)
	8.2 alias_bool_query_1 (4 clients)
	8.3 alias_bool_query_2 (4 clients)

=============================================
Challenge [index-and-search] (run by default)
=============================================

Index a document corpus, then search

Schedule:
----------

1. delete-index
2. delete-data-stream-gharchive
3. create-index
4. wait-for-cluster-health-status-green
5. index (8 clients)
6. refresh-after-index
7. default
8. default_1k
```

### Data streams

```shell
Showing details for track [github_archive]:

* Description: GitHub timeline from gharchive.org
* Documents: 21,435,282
* Compressed Size: 7.6 GB
* Uncompressed Size: 107.3 GB

======================
Challenge [index-only]
======================

Index the document corpus

Schedule:
----------

1. delete-index-gharchive
2. delete-all-data-streams
3. delete-all-templates
4. create-all-templates
5. wait-for-cluster-health-status-green
6. index (8 clients)

========================================
Challenge [parallel-indexing-and-search]
========================================

Index the document corpus, then perform parallel indexing and search operations

Schedule:
----------

1. delete-index-gharchive
2. delete-all-data-streams
3. delete-all-templates
4. create-all-templates
5. wait-for-cluster-health-status-green
6. index_corpora1 (8 clients)
7. refresh-after-index
8. add_filter_alias
9. 3 parallel tasks (16 clients):
	9.1 index_corpora2_parallel_task (8 clients)
	9.2 alias_bool_query_1 (4 clients)
	9.3 alias_bool_query_2 (4 clients)

=============================================
Challenge [index-and-search] (run by default)
=============================================

Index a document corpus, then search

Schedule:
----------

1. delete-index-gharchive
2. delete-all-data-streams
3. delete-all-templates
4. create-all-templates
5. wait-for-cluster-health-status-green
6. index (8 clients)
7. refresh-after-index
8. default
9. default_1k
```

### License

Content based on [www.gharchive.org](https://www.gharchive.org) used under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) license.
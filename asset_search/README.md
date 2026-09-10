# asset_search

A Rally benchmark track for a large-scale design asset search workload. Models a single document type — design assets — with realistic field cardinality for workspace, team, owner, and folder entities. Covers both high-throughput reload ingest and concurrent steady-state ingest + search.

## Document schema

Documents index into a single alias (`rally-asset-search`, backed by `rally-asset-search-v1`) with `dynamic: strict`.

| Field | ES type | Notes |
|---|---|---|
| `asset_id` | keyword | UUID |
| `title` | text | 4–8 word sentence |
| `description` | text | Up to 280 chars |
| `content` | text | Up to 250 chars |
| `asset_type` | keyword | One of: `design`, `image`, `video`, `presentation`, `document` |
| `owner_id` | keyword | UUID drawn from bounded owner pool |
| `team_id` | keyword | UUID drawn from bounded team pool |
| `workspace_id` | keyword | UUID drawn from bounded workspace pool |
| `folder_id` | keyword | UUID drawn from bounded folder pool |
| `tags` | keyword[] | 2–5 entries drawn from a fixed 20-tag vocabulary |
| `status` | keyword | `published` (70%), `draft` (20%), `archived` (10%) |
| `created_at` | date | Random within `date_range_days` before now |
| `updated_at` | date | `created_at` + up to 30 days, capped at now |
| `view_count` | integer | 0–1,000,000 |
| `file_size_bytes` | long | 10 KB–100 MB |

Entity ID pools (workspace, team, owner, folder) are generated deterministically from bounded UUID pools seeded at fixed offsets from the base seed. This ensures realistic field cardinality — the same entity IDs recur across documents and across runs — without introducing fully random UUIDs that would defeat filter caching.

## Challenges

### `index-and-search` (default)

Creates the index template, versioned index, and alias; bulk-indexes all documents; then runs the full search mix in parallel.

### `reload`

Creates a fresh versioned index with `refresh_interval: -1` for maximum ingest throughput, bulk-indexes the full dataset, then stops. Use this to populate an index before running `search-only`.

### `reload-and-steady-state`

Phase 1: high-throughput reload with `refresh_interval: -1`. Phase 2: transitions to steady-state index settings, then runs concurrent steady-state ingest (`bulk-index-new`, `date-range-days: 1`) and the full search mix in parallel. Terminates when the ingest operation exhausts its document count.

### `search-only`

Runs the search mix against an already-indexed dataset. No indexing.

## Search operations

| Operation | Query shape | Weight |
|---|---|---|
| `match-title` | `match` on `title` | 8 |
| `match-content` | `match` on `content` | 8 |
| `bool-filter` | `bool` must: `term` asset_type + `term` status; filter: `range` created_at (90d) | 8 |
| `bool-text-filter` | `bool` must: `match` title; filter: `term` status + `range` created_at (30d) | 8 |
| `query-string-content` | `query_string` across `title`, `description`, `content` | 6 |
| `term-asset-type` | `term` on `asset_type` | 5 |
| `term-status` | `term` on `status` | 5 |
| `range-created-at` | Date range: last 30 days | 5 |
| `phrase-title` | `match_phrase` on `title` | 5 |
| `desc-sort-created-at` | `match_all`, sort by `created_at` desc | 5 |
| `desc-sort-view-count` | `term` status=published, sort by `view_count` desc; `track_total_hits: false` | 5 |
| `keyword-terms-asset-type` | Terms aggregation on `asset_type` | 4 |
| `keyword-terms-status` | Terms aggregation on `status` | 4 |
| `date-histogram-created-at` | Date histogram on `created_at`, `calendar_interval: day` | 4 |
| `date-histogram-with-filter` | Date range (30d) + date histogram with `avg` view_count and `sum` file_size_bytes sub-aggs | 4 |
| `tags-terms` | Terms aggregation on `tags`, size 20 | 4 |
| `range-view-count` | Range on `view_count` (100–10,000) | 3 |
| `asc-sort-created-at` | `match_all`, sort by `created_at` asc | 3 |
| `multi-terms-type-status` | Multi-terms aggregation on `asset_type` + `status` | 3 |
| `range-file-size` | Range on `file_size_bytes` (100 KB–10 MB) | 2 |
| `match-all` | `match_all` | 1 |

## Track parameters

All parameters are optional. Pass via `--track-params="key:value,..."`.

### Index and mapping

| Parameter | Default | Description |
|---|---|---|
| `index_name` | `rally-asset-search` | Alias name; versioned index is `<name>-v1` |
| `number_of_shards` | `1` | Primary shard count. Omitted from the index template when `build_flavor=serverless` and `serverless_operator=false` — leave unset to use the Serverless default. |
| `number_of_replicas` | `0` | Replica count. Always omitted when `build_flavor=serverless` — setting replicas on Serverless requires operator privileges and is managed by the platform. |
| `build_flavor` | `stateful` | Set to `serverless` when targeting an Elasticsearch Serverless endpoint. Guards shard/replica settings that are restricted or unsupported on Serverless. |
| `serverless_operator` | `false` | Set to `true` when running as a Serverless operator user (internal Elastic). Allows `number_of_shards` to be set in the index template. Has no effect when `build_flavor` is not `serverless`. |

### Document generation

| Parameter | Default | Description |
|---|---|---|
| `number_of_docs` | `1_000_000` | Total docs for `bulk-index` (across all clients) |
| `reload_number_of_docs` | `10_000_000` | Total docs for `bulk-index-reload` |
| `ingest_number_of_docs` | `10_000_000` | Total docs for `bulk-index-new` (steady-state) |
| `bulk_size` | `500` | Docs per bulk request for standard ingest |
| `reload_bulk_size` | `1_000` | Docs per bulk request for reload |
| `seed` | `42` | Base RNG seed for standard ingest |
| `reload_seed` | `100` | Base RNG seed for reload (avoids overlap with `seed`) |
| `ingest_seed` | `42` | Base RNG seed for steady-state ingest |
| `date_range_days` | `730` | Spread of `created_at` timestamps before now |

### Entity pool cardinality

Controls how many distinct UUIDs exist in each bounded pool. Higher values reduce filter selectivity; lower values increase it.

| Parameter | Default | Field(s) |
|---|---|---|
| `num_workspaces` | `10_000` | `workspace_id` |
| `num_teams` | `50_000` | `team_id` |
| `num_owners` | `200_000` | `owner_id` |
| `num_folders` | `500_000` | `folder_id` |

### Ingest performance

| Parameter | Default | Description |
|---|---|---|
| `bulk_indexing_clients` | `8` | Parallel clients for standard bulk ingest |
| `reload_clients` | `16` | Parallel clients for reload |
| `ingest_target_throughput` | _(unset)_ | Docs/s cap for standard ingest; omit for max throughput |
| `reload_target_throughput` | _(unset)_ | Docs/s cap for reload; omit for max throughput |
| `retries_on_429` | `10` | Retry count on HTTP 429 for all bulk operations |
| `error_level` | `non-fatal` | `non-fatal` or `fatal`; controls bulk error handling |

### Index settings (reload vs. steady-state)

| Parameter | Default | Description |
|---|---|---|
| `reload_refresh_interval` | `-1` | Refresh interval applied before reload ingest. `-1` (disabled) is valid on both stateful and Serverless. If setting a positive value on Serverless, minimum is `5s`. |
| `reload_translog_durability` | _(unset)_ | Optional translog durability override for reload |
| `reload_number_of_replicas` | _(unset)_ | Optional replica count override during reload. Ignored when `build_flavor=serverless`. |
| `steady_state_refresh_interval` | _(unset)_ | Refresh interval applied after reload completes. If unset, no refresh interval change is made and the index retains whatever value is in effect. Serverless enforces a minimum of `5s` for positive values; `-1` is valid on both. |
| `steady_state_translog_durability` | _(unset)_ | Optional translog durability for steady-state |
| `steady_state_number_of_replicas` | _(unset)_ | Optional replica count for steady-state. Ignored when `build_flavor=serverless`. |

### Search

| Parameter | Default | Description |
|---|---|---|
| `search_clients` | `8` | Parallel search clients |
| `warmup_iterations` | `500` | Warmup iterations before measurement |
| `search_iterations` | `1_000` | Measured iterations |

## Dependencies

`faker` is declared in `track.json` under `dependencies` and is installed automatically by Rally at race time.

## Example invocations

Smoke test (small doc count, reduced iterations):

```bash
esrally race \
  --track-path=~/repos/rally-tracks/asset_search \
  --pipeline=benchmark-only \
  --target-hosts=<endpoint>:443 \
  --client-options="use_ssl:true,verify_certs:true,basic_auth_user:'<user>',basic_auth_password:'<pass>'" \
  --challenge=index-and-search \
  --track-params="number_of_docs:100000,bulk_size:500,bulk_indexing_clients:4,search_clients:4,warmup_iterations:50,search_iterations:100"
```

Single-shard reload at max throughput (ECH or stateful):

```bash
esrally race \
  --track-path=~/repos/rally-tracks/asset_search \
  --pipeline=benchmark-only \
  --target-hosts=<endpoint>:443 \
  --client-options="use_ssl:true,verify_certs:true,basic_auth_user:'<user>',basic_auth_password:'<pass>'" \
  --challenge=reload \
  --track-params="reload_number_of_docs:120000000,reload_clients:16,number_of_shards:1,number_of_replicas:1"
```

Reload then search-only (two-phase, Serverless):

```bash
# Phase 1: populate
esrally race \
  --track-path=~/repos/rally-tracks/asset_search \
  --pipeline=benchmark-only \
  --target-hosts=<endpoint>:443 \
  --client-options="use_ssl:true,verify_certs:true,basic_auth_user:'<user>',basic_auth_password:'<pass>'" \
  --challenge=reload \
  --track-params="reload_number_of_docs:50000000,reload_clients:16,number_of_shards:5"

# Phase 2: search load
esrally race \
  --track-path=~/repos/rally-tracks/asset_search \
  --pipeline=benchmark-only \
  --target-hosts=<endpoint>:443 \
  --client-options="use_ssl:true,verify_certs:true,basic_auth_user:'<user>',basic_auth_password:'<pass>'" \
  --challenge=search-only \
  --track-params="search_clients:16,warmup_iterations:500,search_iterations:2000"
```

Reload + concurrent steady-state ingest and search:

```bash
esrally race \
  --track-path=~/repos/rally-tracks/asset_search \
  --pipeline=benchmark-only \
  --target-hosts=<endpoint>:443 \
  --client-options="use_ssl:true,verify_certs:true,basic_auth_user:'<user>',basic_auth_password:'<pass>'" \
  --challenge=reload-and-steady-state \
  --track-params="reload_number_of_docs:10000000,reload_clients:16,ingest_number_of_docs:5000000,bulk_indexing_clients:8,search_clients:8"
```

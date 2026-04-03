# Has-Privileges Bystander Blocking Track

Demonstrates Netty event-loop head-of-line blocking caused by expensive `_has_privileges` index privilege evaluation.

## What This Track Shows

When a `_has_privileges` request triggers expensive DFA (automaton) operations in `IndicesPermission.checkResourcePrivileges`, it blocks the Netty event loop thread synchronously. Any other HTTP request ("bystander") bound to the same event loop must wait in line, causing latency outliers unrelated to the bystander request's own cost.

The track runs `_has_privileges` requests alongside trivial `GET /` bystander requests on a single Netty event loop, then compares their latency distributions. A successful reproduction shows bystander p100 latency approaching `has_privileges` p100.

## Cluster Prerequisites

The target Elasticsearch cluster must be configured with the following **static** settings in `elasticsearch.yml` (requires node restart):

```yaml
http.netty.worker_count: 1
```

This forces all HTTP connections onto a single Netty event loop thread, making the blocking effect deterministic. Without this, blocking still occurs but only affects the ~1/N fraction of bystander requests that happen to land on the same event loop as a slow `has_privileges` request.

The track validates this setting at startup and fails with a clear error if it is not configured.

X-Pack Security must be enabled (default in recent ES versions).

## Parameters

All parameters can be configured via `--track-params`:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `num_roles` | integer | 100 | Number of roles to create (more roles = more index privilege groups to evaluate) |
| `num_users` | integer | 1 | Number of test users |
| `num_roles_per_user` | integer | 100 | Roles assigned per user (must be <= `num_roles`) |
| `wildcard_mode` | string | `"both"` | Index pattern wildcards: `both`, `prefix`, `suffix`, or `none` |
| `index_privileges_per_role` | integer | 10 | Index privilege entries per role |
| `iterations` | integer | 100 | Number of `has_privileges` requests to measure |
| `warmup_iterations` | integer | 3 | Warmup iterations before measurement |
| `has_privileges_clients` | integer | 1 | Concurrent `has_privileges` clients |
| `bystander_clients` | integer | 1 | Concurrent bystander (`GET /`) clients |

### Wildcard Modes

| Mode | Pattern | Description |
|---|---|---|
| `both` | `*abc123*` | Both prefix and suffix wildcards (most expensive) |
| `prefix` | `*abc123` | Prefix wildcard only |
| `suffix` | `abc123*` | Suffix wildcard only |
| `none` | `abc123` | No wildcards (cheapest) |

## Usage

### With External Cluster (benchmark-only)

```bash
esrally race --track-path=has_privileges_bystander \
  --pipeline=benchmark-only \
  --target-hosts=http://localhost:9200 \
  --client-options="basic_auth_user:'elastic',basic_auth_password:'password'" \
  --track-params="iterations:50"
```

### With Rally-Provisioned Cluster

Not directly supported because `http.netty.worker_count` is a static setting that must be in `elasticsearch.yml` before the node starts. You would need a custom car definition that includes this setting.

## How It Works

1. **`check_netty_worker_count`** -- verifies `http.netty.worker_count: 1` on all nodes
2. **`create_roles_and_users`** -- creates roles with randomized wildcard index patterns and assigns them to test users
3. **Parallel phase** -- runs concurrently until `has_privileges` completes:
   - **`has_privileges`** -- sends `_has_privileges` requests with a large, unique request body (50 index expressions with wildcard patterns, 10 cluster privileges). Each body is randomized to defeat the per-role `hasPrivilegesCache`.
   - **`cluster_info`** -- sends trivial `GET /` requests continuously as bystander traffic

## Interpreting Results

| Metric | What to look for |
|---|---|
| `has_privileges` p50 | Baseline cost of index privilege evaluation (~2s with defaults) |
| `cluster_info` p50 | Should be <1ms (trivial request, no contention) |
| `cluster_info` p100 | Should approach `has_privileges` p100 (proves blocking) |

If `cluster_info` p100 is close to `has_privileges` p100, a bystander request was blocked behind a full `_has_privileges` evaluation on the shared event loop.

## Cost Center

JFR profiling confirms ~90% of CPU on `http_server_worker[T#1]` is spent in:

- `Automatons.subsetOf` -- tandem DFA walk checking if requested index patterns are subsets of granted patterns (called from `IndicesPermission.checkResourcePrivileges`)
- `Automatons.minusAndMinimize` -- DFA complement-intersection + Hopcroft minimization to compute ungrantable privileges (called from `IndicesPermission.checkResourcePrivileges`)
- `Automaton.getSortedTransitions` -- materializing sorted transition tables consumed by `subsetOf`

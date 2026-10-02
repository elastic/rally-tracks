# Has-Privileges Bystander Blocking Track

Benchmarks expensive `_has_privileges` requests alongside lightweight bystander requests to measure head-of-line blocking on Netty event-loop threads.

## What This Track Shows

When a `_has_privileges` request triggers expensive DFA (automaton) operations in `IndicesPermission.checkResourcePrivileges`, it can block the Netty event loop thread synchronously. Any other HTTP request ("bystander") bound to the same event loop must wait in line, causing latency outliers unrelated to the bystander request's own cost.

The track runs expensive `_has_privileges` requests alongside lightweight bystander requests, then compares their latency distributions. Head-of-line blocking manifests as bystander p100 latency approaching `has_privileges` p100.

## Cluster Prerequisites

X-Pack Security must be enabled (default in recent ES versions). No special static settings are required.

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
| `bystander_clients` | integer | 1 | Concurrent bystander (`GET /`) clients (used when `cached_bystander_clients` is 0) |
| `cached_bystander_clients` | integer | 0 | Concurrent bystander clients using lightweight cached `_has_privileges` requests instead of `GET /` |

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

## How It Works

1. **`create_roles_and_users`** -- creates roles with randomized wildcard index patterns and assigns them to test users. If `cached_bystander_clients > 0`, also creates a `bystander_user` with a single simple role.
2. **Parallel phase** -- runs concurrently until `has_privileges` completes:
   - **`has_privileges`** -- sends `_has_privileges` requests with a large, unique request body (50 index expressions with wildcard patterns, 10 cluster privileges). Each body is randomized to defeat the per-role `hasPrivilegesCache`.
   - **`has_privileges_cached`** (when `cached_bystander_clients > 0`) -- sends lightweight `_has_privileges` requests as `bystander_user` with a simple cached role. These hit the role cache and complete quickly unless blocked.
   - **`cluster_info`** (when `cached_bystander_clients == 0`) -- sends trivial `GET /` requests continuously as bystander traffic.

## Interpreting Results

| Metric | What to look for |
|---|---|
| `has_privileges` p50 | Baseline cost of index privilege evaluation (~2s with defaults) |
| bystander p50 | Should be <1ms (trivial request, no contention) |
| bystander p100 | Approaches `has_privileges` p100 when head-of-line blocking is present |

If bystander p100 is close to `has_privileges` p100, a bystander request was blocked behind a full `_has_privileges` evaluation on the shared Netty event loop.

## Comparison Benchmarking

To compare two ES builds (e.g., a baseline release vs. a branch with a fix), run the track against each build with a tagged `--race-id`, then use `esrally compare`.

### 1. Run the baseline

Start the baseline ES (e.g., 9.3.3), then:

```bash
esrally race --track-path=has_privileges_bystander \
  --pipeline=benchmark-only \
  --target-hosts=http://localhost:9200 \
  --client-options="basic_auth_user:'elastic',basic_auth_password:'password'" \
  --track-params='{"cached_bystander_clients": 8, "has_privileges_clients": 2, "iterations": 10, "warmup_iterations": 1}' \
  --on-error=abort \
  --race-id=baseline-933 \
  --user-tag="version:9.3.3"
```

### 2. Run the contender

Stop the baseline, start the contender ES, then run the same command with a different `--race-id` and `--user-tag`:

```bash
esrally race --track-path=has_privileges_bystander \
  --pipeline=benchmark-only \
  --target-hosts=http://localhost:9200 \
  --client-options="basic_auth_user:'elastic',basic_auth_password:'password'" \
  --track-params='{"cached_bystander_clients": 8, "has_privileges_clients": 2, "iterations": 10, "warmup_iterations": 1}' \
  --on-error=abort \
  --race-id=contender-branch \
  --user-tag="version:my-branch"
```

### 3. Compare

```bash
esrally compare --baseline=baseline-933 --contender=contender-branch
```

### Key metrics to watch

| Metric | Indicates |
|---|---|
| `has_privileges` p50/p100 | Cost of the expensive authorization path |
| `has_privileges_cached` p50 | Steady-state bystander latency (should be sub-ms) |
| `has_privileges_cached` p100 | Worst-case bystander latency -- drops dramatically when head-of-line blocking is eliminated |
| `has_privileges_cached` throughput | Bystander throughput under contention |
| error rate | Non-zero on either task indicates a functional regression (e.g., auth context leak) |

A successful fix for head-of-line blocking shows bystander p100 dropping from ~2s (matching `has_privileges` latency) to sub-200ms, while bystander p50 stays sub-millisecond.

## Cost Center

JFR profiling confirms ~90% of CPU on `http_server_worker[T#1]` is spent in:

- `Automatons.subsetOf` -- tandem DFA walk checking if requested index patterns are subsets of granted patterns (called from `IndicesPermission.checkResourcePrivileges`)
- `Automatons.minusAndMinimize` -- DFA complement-intersection + Hopcroft minimization to compute ungrantable privileges (called from `IndicesPermission.checkResourcePrivileges`)
- `Automaton.getSortedTransitions` -- materializing sorted transition tables consumed by `subsetOf`

# Search Shard Offline Warming Track

This track benchmarks the effectiveness of offline blob cache warming during search shard recovery in serverless Elasticsearch.

## What it tests

When a search shard relocates to a new node in serverless Elasticsearch, it must recover by reading segment data from the object store (or indexing shard) into the local shared blob cache. **Offline warming** (`stateless.search.offline_warming.enabled`) pre-populates this cache during recovery so that search queries hitting the newly-recovered shard don't suffer cold-cache latencies.

This track measures how well that warming works by comparing search latency **before** shard relocation (fully warm cache) against latency **immediately after** relocation (where the cache was warmed offline during recovery).

## Data corpus

Uses the [PMC (PubMed Central)](https://rally-tracks.elastic.co/pmc) corpus: ~574K academic paper documents (~23 GB uncompressed). This provides a realistic full-text search workload.

## Challenges

### `offline-warming-benchmark` (default)

The primary benchmark. Phases:

1. **Ingest** - Bulk index the full PMC corpus, force-merge, and wait for merges to complete.
2. **Baseline** - Run each query type with warmup iterations to establish warm-cache latency (p50/p99).
3. **Relocate** - Force shard relocation via allocation exclusion, triggering search shard recovery and offline warming.
4. **Post-relocation** - Run the same queries with zero warmup immediately after recovery completes. Compare latencies against baseline.
5. **Cleanup** - Clear allocation exclusions.

### `offline-warming-repeated-relocations`

Runs 3 successive relocation rounds with search measurements between each. Useful for observing whether warming effectiveness is consistent across multiple recovery cycles.

### `baseline-only`

Control benchmark: indexes data and runs searches without any relocation. Use to establish a pure baseline for comparison.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `target_index` | `search_shard_warming` | Index name |
| `number_of_shards` | `1` | Number of primary shards |
| `number_of_replicas` | `0` | Number of replica shards |
| `bulk_size` | `500` | Documents per bulk request |
| `bulk_indexing_clients` | `8` | Concurrent indexing clients |
| `ingest_percentage` | `100` | Percentage of corpus to ingest |
| `baseline_warmup_iterations` | `200` | Warmup iterations for baseline searches |
| `baseline_iterations` | `500` | Measured iterations for baseline searches |
| `baseline_throughput` | `20` | Target ops/s for baseline searches |
| `post_relocate_iterations` | `500` | Measured iterations for post-relocation searches |
| `post_relocate_throughput` | `20` | Target ops/s for post-relocation searches |
| `recovery_timeout` | `300` | Max seconds to wait for recovery |
| `recovery_poll_interval` | `2` | Seconds between recovery status polls |
| `shard_id` | `0` | Shard number to relocate |
| `max_num_segments` | `-1` | Force-merge target segments (-1 = default) |
| `post_ingest_sleep` | `false` | Whether to sleep after ingest |
| `post_ingest_sleep_duration` | `30` | Sleep duration in seconds |

## Prerequisites

- A multi-node Elasticsearch cluster (at least 2 data nodes) so shards can relocate between nodes.
- For serverless testing, the cluster should have `stateless.search.offline_warming.enabled: true` (the default).

## Usage

```bash
# Run the default offline warming benchmark
esrally race --track-path=/path/to/search_shard_warming --challenge=offline-warming-benchmark

# Run baseline-only for comparison
esrally race --track-path=/path/to/search_shard_warming --challenge=baseline-only

# Run with custom parameters
esrally race --track-path=/path/to/search_shard_warming \
  --track-params="number_of_shards:2,baseline_iterations:1000,post_relocate_iterations:1000"

# Run repeated relocations
esrally race --track-path=/path/to/search_shard_warming --challenge=offline-warming-repeated-relocations
```

## Interpreting results

Compare the service time (p50, p99) of each query type across phases:

- `baseline-*` operations represent warm-cache performance.
- `post-relocate-*` operations represent performance after offline warming during recovery.

If offline warming is effective, post-relocation latencies should be close to baseline. A large gap indicates the cache was not fully warmed during recovery.

## Custom runners

The track registers these custom operation types in `track.py`:

- `relocate-shard` - Forces shard relocation via allocation exclusion or cluster reroute.
- `wait-for-recovery` - Polls the recovery API until shard recovery completes.
- `clear-allocation-exclusions` - Removes transient allocation exclusion settings.
- `wait-for-green` - Waits for cluster health to reach green with no relocating shards.
- `record-shard-stats` - Captures index-level stats (store size, cache sizes, query counts) for diagnostics.

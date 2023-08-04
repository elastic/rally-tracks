# Kubernetes (K8s) Metrics Track
K8s Metrics is a track intended for benchmarking refresh on Elasticsearch using a Kubernetes pod metrics dataset. A small corpus of Kibana object definition documents is included for indexing with fast refresh enabled.

## Track Parameters

| Setting | Default | Description |
| --- | --- | --- |
| `bulk_indexing_clients` | `8` | The number of bulk indexing clients. |
| `bulk_refresh` | `unset` | Control the refresh behavior for bulk requests. Valid values are `true`, `wait_for`, `false`, or unset. This parameter is always specified as a string. |
| `bulk_size` | `1000` | The batch size of bulk requests. |
| `fast_refresh_bulk_size` | `15` | The bulk batch size of the fast refresh index. |
| `fast_refresh_clients` | `1` | The number of bulk indexing clients for fast refresh indexing. |
| `fast_refresh_indexing_throughput` | `2.7` | The throughput, in operations per second, for fast refresh indexing. |
| `ingest_percentage` | `100` | The percentage of the document corpus to index. |
| `manual_refresh_clients` | `1` | The number of clients to use for manual refresh operations. |
| `manual_refresh_interval` | `15` | The interval, in seconds, for issuing manual refresh requests. |
| `number_of_replicas` | `1` | The number of replicas to allocate to the corpus data stream. |
| `number_of_shards` | `1` | The number of shards to allocate to the corpus data stream. |
| `refresh_interval` | `unset` | The target data stream refresh interval; e.g., `5s`. If unset, the Elasticsearch default refresh interval is used. |

## Challenges

### `append-no-conflicts-metrics-index-with-refresh` (default)

Index a metrics document corpus and sets the bulk API `refresh` query parameter. By default, Elasticsearch will perform refreshes asynchronously. This challenge is intended to capture refresh latency and throughput impact of refreshes during bulk indexing. This challenge can be executed against both stateful and serverless Elasticsearch.

#### Parameters

* `bulk_indexing_clients` (default: `8`)
* `bulk_refresh` (default: `"true"`)
* `bulk_size` (default: `1000`)
* `ingest_percentage` (default: `100`)
* `number_of_replicas` (default: `1`)
* `number_of_shards` (default: `1`)

### `append-no-conflicts-metrics-index-with-intermittent-refresh`

Index a metrics document corpus while performing intermittent manual refreshes of the target data stream at the specified interval. This challenge is intended to capture refresh latency and the indexing throughput impact of refreshes. This challenge can be executed against both stateful and serverless Elasticsearch.

#### Parameters

* `bulk_indexing_clients` (default: `8`)
* `bulk_size` (default: `1000`)
* `ingest_percentage` (default: `100`)
* `manual_refresh_clients` (default: `1`)
* `manual_refresh_interval` (default: `15`)
* `number_of_replicas` (default: `1`)
* `number_of_shards` (default: `1`)
* `refresh_interval` (default: `unset`)

### `append-no-conflicts-metrics-index-only`

Index a metrics document corpus. This challenge can be used as a baseline when comparing benchmarking results with other refresh-oriented track challenges. This challenge can be executed against both stateful and serverless Elasticsearch.

#### Parameters

* `bulk_indexing_clients` (default: `8`)
* `bulk_size` (default: `1000`)
* `ingest_percentage` (default: `100`)
* `number_of_replicas` (default: `1`)
* `number_of_shards` (default: `1`)
* `refresh_interval` (default: `unset`)

### `append-no-conflicts-metrics-with-fast-refresh`

Index a metrics document corpus while indexing a small Kibana corpus to a separate fast refresh index. This challange simulates indexing to a smaller index with fast refresh enabled at 3 documents per second (default) while concurrently bulk indexing to a larger data stream. The race ends once all fast refresh documents have been indexed. This challenge can be executed against serverless Elasticsearch and requires the `kibana_system` security role for the authenticated user.

#### Parameters

* `bulk_indexing_clients` (default: `8`)
* `bulk_size` (default: `1000`)
* `ingest_percentage` (default: `100`)
* `fast_refresh_bulk_size` (default: `15`)
* `fast_refresh_clients` (default: `1`)
* `fast_refresh_indexing_throughput` (default: `2.7`)
* `number_of_replicas` (default: `1`)
* `number_of_shards` (default: `1`)
* `refresh_interval` (default: `unset`)

### `fast-refresh-index-only`

Index a small Kibana corpus to a system index with fast refresh enabled. This challenge can be executed against serverless Elasticsearch and requires the `kibana_system` security role for the authenticated user.

#### Parameters

* `fast_refresh_bulk_size` (default: `15`)
* `fast_refresh_clients` (default: `1`)
* `fast_refresh_indexing_throughput` (default: `2.7`)

### `fast-refresh-index-with-search`

Index a small Kibana corpus to a system index with fast refresh enabled, and simultaneously perform searches on the index. This challenge can be executed against serverless Elasticsearch and requires the `kibana_system` security role for the authenticated user.

#### Parameters

* `fast_refresh_bulk_size` (default: `15`)
* `fast_refresh_clients` (default: `1`)
* `fast_refresh_indexing_throughput` (default: `2.7`)
# Serverless Kubernetes Track
Serverless Kubernetes is a track intended for benchmarking serverless Elasticsearch using a Kubernetes pod metrics dataset. A small corpus of Kibana object definitions is included for indexing with fast refresh enabled.

## Track Parameters

| Setting | Default | Description |
| --- | --- | --- |
| `bulk_indexing_clients` | `8` | The number of bulk indexing clients. |
| `bulk_size` | `1000` | The batch size of bulk requests. |
| `fast_refresh_bulk_size` | `1` | The bulk batch size of the fast refresh index. |
| `fast_refresh_clients` | `1` | The number of bulk indexing clients for fast refresh indexing. |
| `fast_refresh_indexing_interval` | `15` | The interval, in seconds, for indexing to the fast refresh index. |
| `ingest_percentage` | `100` | The percentage of the document corpus to index. |
| `manual_refresh_clients` | `1` | The number of clients to use for manual refresh operations. |
| `manual_refresh_interval` | `15` | The interval, in seconds, for issuing manual refresh requests. |
| `number_of_replicas` | `1` | The number of replicas to allocate to the corpus data stream. |
| `number_of_shards` | `1` | The number of shards to allocate to the corpus data stream. |

## Challenges

### `append-no-conflicts-metrics-index-with-refresh` (default)

Index a metrics document corpus while performing intermittent manual refreshes of the target data stream at the specified interval. This challenge is intended to capture refresh latency and the indexing throughput impact of refreshes.

#### Parameters

* `bulk_indexing_clients` (default: `8`)
* `ingest_percentage` (default: `100`)
* `manual_refresh_clients` (default: `1`)
* `manual_refresh_interval` (default: `15`)
* `number_of_replicas` (default: `1`)
* `number_of_shards` (default: `1`)

### `append-no-conflicts-metrics-index-only`

Index a metrics document corpus. This challenge can be used as a baseline when comparing benchmarking results with other refresh-oriented track challenges.

#### Parameters

* `bulk_indexing_clients` (default: `8`)
* `ingest_percentage` (default: `100`)
* `number_of_replicas` (default: `1`)
* `number_of_shards` (default: `1`)

### `append-no-conflicts-metrics-with-fast-refresh`

Index a metrics document corpus while indexing a small Kibana corpus to a separate fast refresh index. This challange simulates indexing to a smaller index with fast refresh enabled while concurrently bulk indexing to a larger data stream.

#### Parameters

* `bulk_indexing_clients` (default: `8`)
* `ingest_percentage` (default: `100`)
* `fast_refresh_clients` (default: `1`)
* `fast_refresh_indexing_interval` (default: `15`)
* `number_of_replicas` (default: `1`)
* `number_of_shards` (default: `1`)
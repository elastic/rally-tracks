## EQL track

This track contains endgame data from SIEM demo cluster and can be downloaded from: https://rally-tracks.elastic.co/eql/endgame-4.28.2-000001-documents.json.bz2
(The 1k test file can be downloaded from https://rally-tracks.elastic.co/eql/endgame-4.28.2-000001-documents-1k.json.bz2)

### Parameters

This track allows to overwrite the following parameters using `--track-params`:

* `bulk_size` (default: 5000)
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `number_of_replicas` (default: 0)
* `number_of_shards` (default: 5)
* `index_settings`: A list of index settings. Index settings defined elsewhere (e.g. `number_of_replicas`) need to be overridden explicitly.
* `cluster_health` (default: "green"): The minimum required cluster health.
* `error_level` (default: "non-fatal"): Available for bulk operations only to specify ignore-response-error-level.
* `cluster` (default: '') Cluster name configured on the target ES host as a remote cluster to allow execution of CCS queries.

### Query Selection

The queries have been selected using the following criterias:

* **Isolation**: A query should capture the performance impact of an individual feature or a specific invocation of a feature.
* **Focus on EQL**: The main focus is to test language features specific to EQL and not features of ES itself.
* **Runtime**: Queries should not run longer than ~3s to reach a target throughput of at least 0.3qps. Because we aim to have at least 50 iterations of each query per nightly run to get enough statistical information, longer running queries would become too expensive.

### Challenge Configuration

The newer tasks in this track aim to measure the request latency and not the maximal throughput. This assumes that the main access pattern for EQL is interactive where one or more users issue successive requests (as opposed to a batch process that maximizes query throughput). Hence, they use the `target-throughput` property to avoid congestion. The `target-throughput` should be chosen low enough such that it can be met by the benchmark (check whether it matches the Max Throughput statistic in the report).

The `warmup-iterations` property has been chosen such that the measurement phase sees stable response times. This can be verified by analyzing the reported measurements in the `rally-metrics-*` index (or by checking that the 95th percentile is close to the median).
# SQL Track

Track for measuring SQL query performance. This track uses the same corpora as the NOAA track. See [../noaa/README.md](../noaa/README.md) for more details on how to generate the dataset and for example records.

## Parameters

This track allows to overwrite the following parameters using `--track-params`:

* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `number_of_replicas` (default: 0)
* `number_of_shards` (default: 1)
* `index_settings`: A list of index settings. Index settings defined elsewhere (e.g. `number_of_replicas`) need to be overridden explicitly.
* `max_num_segments` (default: 1)
* `query_percentage` (default: 100): Factor applied to the number of warmup-iterations and iterations for queries. Useful to run quick experiments but watch out for effects due to the shorter warmup period!

## Query Selection

The queries have been selected using the following criterias:

* **Isolation**: A query should capture the performance impact of an individual feature or a specific invocation of a feature.
* **Focus on SQL**: The main focus is to test language features specific to SQL and not features of ES itself.
* **Runtime**: Queries should not run longer than ~1s to reach a target throughput of at least 1qps. Because we aim to have at least 50 iterations of each query per nightly run to get enough statistical information, longer running queries would become too expensive.
## TODO

### Parameters

This track allows to overwrite the following parameters using `--track-params`:

* `bulk_size` (default: 10000)
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested. It will be applied to the main index and to the large join indexes (ie. not to join indexes with up to 500K documents)
* `max_concurrent_shards_per_node` (default 10): A number between 1 and 100 that defines how many concurrent threads will run per query in a node
* `number_of_replicas` (default: 1): This only applies to the main index (not to lookup indexes)
* `number_of_shards` (default: 5): This only applies to the main index (not to lookup indexes)
* `source_mode` (default: stored): Should the `_source` be `stored` to disk exactly as sent (the default), thrown away (`disabled`), or reconstructed on the fly (`synthetic`)
* `index_settings`: A list of index settings. Index settings defined elsewhere need to be overridden explicitly.
* `cluster_health` (default: "green"): The minimum required cluster health.
* `include_non_serverless_index_settings` (default: true for non-serverless clusters, false for serverless clusters): Whether to include non-serverless index settings.
* `auto_expand_replicas` (default: "0-all"): Set the auto_expand_replicas behaviour for lookup indices.
* `query_clients` (default 1): number of queries to be run in parallel


### License

According to the [Open Data Law](https://opendata.cityofnewyork.us/open-data-law/) this data is available as public domain.

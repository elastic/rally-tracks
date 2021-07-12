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

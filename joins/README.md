## JOINS track

This track contains an artificial dataset intended to test JOIN operations with different key cardinalities.

The dataset can be generated using the scripts in the `_tools` directory.

### Example Documents

Main index: 

```json
{
  "id": 56,
  "@timestamp": 946728056,
  "key_1000": "56",
  "key_100000": "56",
  "key_200000": "56",
  "key_500000": "56",
  "key_1000000": "56",
  "key_5000000": "56",
  "key_100000000": "56",
  "field_0": "text with value 0_56",
  "field_1": "text with value 1_56",
  "field_2": "text with value 2_56",
  ...
  "field_99": "text with value 99_56"
}
```

The cardinality of the keys is the same as the key name, eg. `key_1000` will have 1000 different values in the dataset,
from `0` to `999`.
The IDs and the timestamps are sequential.

### Parameters

This track allows to overwrite the following parameters using `--track-params`:

* `bulk_size` (default: 10000)
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested. It will be applied to the main index and to the large join indexes (ie. not to join indexes with up to 500K documents)
* `number_of_replicas` (default: 0)
* `number_of_shards` (default: 1)
* `source_mode` (default: stored): Should the `_source` be `stored` to disk exactly as sent (the default), thrown away (`disabled`), or reconstructed on the fly (`synthetic`)
* `force_merge_max_num_segments` (default: unset): An integer specifying the max amount of segments the force-merge operation should use.
* `index_settings`: A list of index settings. Index settings defined elsewhere (e.g. `number_of_replicas`) need to be overridden explicitly.
* `cluster_health` (default: "green"): The minimum required cluster health.
* `error_level` (default: "non-fatal"): Available for bulk operations only to specify ignore-response-error-level.
* `detailed_results` (default: `false`): Adds additional [metadata](https://esrally.readthedocs.io/en/latest/track.html?highlight=detailed-results#meta-data) to challenges using the track `update` operation. Be aware using this option can add client side overhead due to the deserialization of API responses.
* `include_non_serverless_index_settings` (default: true for non-serverless clusters, false for serverless clusters): Whether to include non-serverless index settings.
* `include_force_merge` (default: true for non-serverless clusters, false for serverless clusters): Whether to include force merge operation.
* `include_target_throughput` (default: true for non-serverless clusters, false for serverless clusters): Whether to apply target throughput.


### License

According to the [Open Data Law](https://opendata.cityofnewyork.us/open-data-law/) this data is available as public domain.

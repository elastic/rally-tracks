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
from `0` to `999` (unless the dataset is not big enough to contain all the keys of a given cardinality, 
eg. with a dataset of 1000 documents, `key_100000000` will contain only 1000 distinct keys, one per document).
The IDs and the timestamps are sequential.

### Parameters

This track allows to overwrite the following parameters using `--track-params`:

* `bulk_size` (default: 10000)
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested. It will be applied to the main index and to the large join indexes (ie. not to join indexes with up to 500K documents)
* `number_of_replicas` (default: 1): This only applies to the main index (not to lookup indexes)
* `number_of_shards` (default: 5): This only applies to the main index (not to lookup indexes)
* `source_mode` (default: stored): Should the `_source` be `stored` to disk exactly as sent (the default), thrown away (`disabled`), or reconstructed on the fly (`synthetic`)
* `index_settings`: A list of index settings. Index settings defined elsewhere need to be overridden explicitly.
* `cluster_health` (default: "green"): The minimum required cluster health.
* `include_non_serverless_index_settings` (default: true for non-serverless clusters, false for serverless clusters): Whether to include non-serverless index settings.
* `auto_expand_replicas` (default: "0-all"): Set the auto_expand_replicas behaviour for lookup indices.


### License

According to the [Open Data Law](https://opendata.cityofnewyork.us/open-data-law/) this data is available as public domain.

## NYC taxis track

This track contains the rides that have been performed in yellow taxis in New York in 2015. It can be downloaded from http://www.nyc.gov/html/tlc/html/about/trip_record_data.shtml.

This has only been tested with the 2015 dump, but this should work with any dump of the yellow taxis, and should be easy to adapt to the green taxis.

Once downloaded, you can generate the mappings with:

```
python3 _tools/parse.py mappings
```

And the json documents  can be generated with:

```  
python3 _tools/parse.py json file_name.csv > documents.json
```

Finally the json docs can be compressed with:

```
bzip2 -k documents.json
```

### Example Document

```json
{
  "total_amount": 6.3,
  "improvement_surcharge": 0.3,
  "pickup_location": [
    -73.92259216308594,
    40.7545280456543
  ],
  "pickup_datetime": "2015-01-01 00:34:42",
  "trip_type": "1",
  "dropoff_datetime": "2015-01-01 00:38:34",
  "rate_code_id": "1",
  "tolls_amount": 0.0,
  "dropoff_location": [
    -73.91363525390625,
    40.76552200317383
  ],
  "passenger_count": 1,
  "fare_amount": 5.0,
  "extra": 0.5,
  "trip_distance": 0.88,
  "tip_amount": 0.0,
  "store_and_fwd_flag": "N",
  "payment_type": "2",
  "mta_tax": 0.5,
  "vendor_id": "2"
}
```

### Parameters

This track allows to overwrite the following parameters with Rally 0.8.0+ using `--track-params`:

* `bulk_size` (default: 10000)
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `conflict_probability` (default: 25): A number between 0 and 100 that defines the probability of id conflicts. Only used by the `update` challenge.
* `on_conflict` (default: "index"): Whether to use an "index" or an "update" action when simulating an id conflict. Only used by the `update` challenge.
* `recency` (default: 0): A number between 0 and 1 that defines whether to bias towards more recent ids when simulating conflicts. See the [Rally docs](http://esrally.readthedocs.io/en/latest/track.html#bulk) for the full definition of this parameter. Only used by the `update` challenge.
* `number_of_replicas` (default: 0)
* `number_of_shards` (default: 1)
* `source_enabled` (default: true): A boolean defining whether the `_source` field is stored in the index.
* `index_settings`: A list of index settings. If it is defined, it replaces *all* other index settings (e.g. `number_of_replicas`).
* `cluster_health` (default: "green"): The minimum required cluster health.

### License

According to the [Open Data Law](https://opendata.cityofnewyork.us/open-data-law/) this data is available as public domain.

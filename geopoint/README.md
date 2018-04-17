## Geopoint track

This track is based on [PlanetOSM](http://wiki.openstreetmap.org/wiki/Planet.osm) data. 

### Example Document

```json
{
  "location": [
    -0.1485188,
    51.5250666
  ]
}
```

### Parameters

This track allows to overwrite the following parameters with Rally 0.8.0+ using `--track-params`:

* `bulk_size` (default: 5000)
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `number_of_replicas` (default: 0)
* `source_enabled` (default: true): A boolean defining whether the `_source` field is stored in the index.
* `index_settings`: A list of index settings. If it is defined, it replaces *all* other index settings (e.g. `number_of_replicas`).
* `cluster_health` (default: "green"): The minimum required cluster health.

### License

Same license as the original data from PlanetOSM: [Open Database License](http://wiki.openstreetmap.org/wiki/Open_Database_License).

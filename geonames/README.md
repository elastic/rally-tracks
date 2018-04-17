## Geonames track

This track is based on a [geonames](http://www.geonames.org/) dump of the file [allCountries.zip](http://download.geonames.org/export/dump/allCountries.zip) retrieved as of April 27, 2017. 

For further details about the semantics of individual fields, please see the [geonames dump README](http://download.geonames.org/export/dump/readme.txt).

Modifications:

* The original CSV data have been converted to JSON.
* We combine the original `longitude` and `latitude` fields to a new `location` field of type [geo_point](https://www.elastic.co/guide/en/elasticsearch/reference/current/geo-point.html).

### Example Document

```json
{
  "geonameid": 2986043,
  "name": "Pic de Font Blanca",
  "asciiname": "Pic de Font Blanca",
  "alternatenames": "Pic de Font Blanca,Pic du Port",
  "feature_class": "T",
  "feature_code": "PK",
  "country_code": "AD",
  "admin1_code": "00",
  "population": 0,
  "dem": "2860",
  "timezone": "Europe/Andorra",
  "location": [
    1.53335,
    42.64991
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

We use the same license for the data as the original data from Geonames:

```
This work is licensed under a Creative Commons Attribution 3.0 License,
see http://creativecommons.org/licenses/by/3.0/
The Data is provided "as is" without warranty or any representation of accuracy, timeliness or completeness.
```
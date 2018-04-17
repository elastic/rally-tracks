## PMC track

This track contains data retrieved from [PMC](https://www.ncbi.nlm.nih.gov/pmc/tools/ftp/).

Note that we have filtered the data set so only a subset of the articles is included. 

### Example Document

Note that the ``body`` content is actually much longer has been shortened here to increase readability.

```json
{
  "name": "3_Biotech_2015_Dec_13_5(6)_1007-1019",
  "journal": "3 Biotech",
  "date": "2015 Dec 13",
  "volume": "5(6)",
  "issue": "1007-1019",
  "accession": "PMC4624133",
  "timestamp": "2015-10-30 20:08:11",
  "pmid": "",
  "body": "\n==== Front\n3 Biotech3 Biotech3 Biotech2190-572X2190-5738Springer ..."
}
```

### Parameters

This track allows to overwrite the following parameters with Rally 0.8.0+ using `--track-params`:

* `bulk_size` (default: 500)
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `number_of_replicas` (default: 0)
* `source_enabled` (default: true): A boolean defining whether the `_source` field is stored in the index.
* `index_settings`: A list of index settings. If it is defined, it replaces *all* other index settings (e.g. `number_of_replicas`).
* [`default_search_timeout`](https://www.elastic.co/guide/en/elasticsearch/reference/6.0/search.html#global-search-timeout) (default: -1)
* `cluster_health` (default: "green"): The minimum required cluster health.

### License

All articles that are included are licensed as CC-BY (http://creativecommons.org/licenses/by/2.0/)

This data set is licensed under the same terms. Please refer to http://creativecommons.org/licenses/by/2.0/ for details.

Attribution hint: 

You can download a full list of the author information for each included document from https://benchmarks.elastic.co/corpora/pmc/attribution.txt.bz2 (size: 52.2MB)

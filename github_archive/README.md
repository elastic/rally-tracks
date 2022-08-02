## GitHub Archive Track

Rally track using data from the [GH Archive](https://www.gharchive.org/) project.

### Track Parameters

Track parameters are specified using `--track-params`; e.g., `--track-params="bulk_size:1000,ingest_percentage:75"`

| Parameter | Default | Description |
| --- | --- | --- |
| `bulk_size` | `5000` | Number of batched documents per bulk request |
| `bulk_indexing_clients` | `8` | Number of clients issuing bulk indexing requests |
| `ingest_percentage` | `100` | A number between 0 and 100 representing how much of the document corpus should be ingested |
| `number_of_shards` | `1` | Number of primary shards to allocate to the index |
| `number_of_replicas` | `1` | Number of replica shards to allocate to the index |
| `codec` | `default` | The index compression codec to use. Use `best_compression` for higher compression at the cost of CPU. |

### License

Content based on [www.gharchive.org](https://www.gharchive.org) used under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) license.
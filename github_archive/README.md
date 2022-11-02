## GitHub Archive Track

Rally track using data from the [GH Archive](https://www.gharchive.org/) project.

### Track Parameters

Track parameters are specified using `--track-params`; e.g., `--track-params="bulk_size:1000,ingest_percentage:75"`

| Parameter | Default | Description |
| --- | --- | --- |
| `bulk_size` | `5000` | Number of batched documents per bulk request |
| `bulk_indexing_clients` | `8` | Number of clients issuing bulk indexing requests |
| `codec` | `default` | The index compression codec to use. Use `best_compression` for higher compression at the cost of CPU. |
| `disable_watermarks` | `false` | Disable the disk allocation decider. |
| `ingest_mode` | `index` | Set to `data_stream` to index to a data stream, otherwise, use a standard index. |
| `ingest_percentage` | `100` | A number between 0 and 100 representing how much of the document corpus should be indexed |
| `max_page_search_size` | `500` | Defines the initial composite aggregation page size for each checkpoint when creating transforms. |
| `number_of_shards` | `1` | Set the number of index primary shards. |
| `number_of_replicas` | `0` | Set the number of replica shards per primary. |
| `source_enabled` | `true` | Set to `false` to disable storing the `_source` field in the index. |

### License

Content based on [www.gharchive.org](https://www.gharchive.org) used under the [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) license.
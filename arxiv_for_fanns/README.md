## arxiv-for-fanns-large track

This track benchmarks filtered approximate nearest neighbor search (FANNS) over a large ArXiv paper embedding dataset.

For more information on the dataset see [the associated ArXiv paper][dataset_paper].

The `arxiv_for_fanns_large` dataset includes over 2.7M vectors of 4096 dimensions, as well as data fields to filter on.
The `queries_emis` file includes 10 000 queries for the exact match in set filter alongside the computed expected
results.

### Example corpus document

```json
{
  "docid": 500000,
  "submitter": "Louis Esperet",
  "has_comments": true,
  "main_categories": ["math"],
  "sub_categories": ["math.CO"],
  "number_of_main_categories": 1,
  "number_of_sub_categories": 1,
  "license": "http://arxiv.org/licenses/nonexclusive-distrib/1.0/",
  "number_of_versions": 3,
  "update_date": 16842,
  "authors": ["Louis Esperet","Pascal Ochem"],
  "number_of_authors": 2,
  "emb": [ 4096 floats ]
}
```

### Example raw query

```json
{
  "emb":[ 4096 floats ],
  "filter":
    {
      "main_categories":"gr-qc"
    },
  "ids":[ 100 integers ]}

```

### Parameters

This track accepts the following parameters with `--track-params`:

- `bulk_size` (default: 500): Documents per bulk request.
- `bulk_indexing_clients` (default: 1): Number of bulk indexing clients.
- `bulk_warmup` (default: 40): Warmup time in seconds for the initial bulk phase.
- `corpora` (default: `"arxiv-for-fanns-large"`): Override the corpus name.
- `index_settings`: Extra index settings merged at create-index time.
- `index_mode`: If set, passed as `index.mode` (e.g. `"vectordb_document"`).
- `max_num_segments` (default: 1): Target segment count for force-merge.
- `number_of_replicas` (default: 0)
- `number_of_shards` (default: 2)
- `post_ingest_sleep` (default: false): Whether to pause after each ingest phase.
- `post_ingest_sleep_duration` (default: 30): Sleep duration in seconds.
- `vector_ef_construction` (default: 100): HNSW `ef_construction`.
- `vector_m` (default: 16): HNSW `m`.
- `vector_index_type` (default: `"bbq_disk"`):
- `vector_similarity` (default: `"cosine"`):

[dataset_paper]: https://arxiv.org/html/2507.21989v1
## arxiv-for-fanns-large track

This track benchmarks filtered approximate nearest neighbor search (FANNS) over a large ArXiv paper embedding dataset.

For more information on the dataset see [the associated ArXiv paper][dataset_paper].

The `arxiv_for_fanns_large` dataset includes over 2.7M vectors of 4096 dimensions, as well as data fields to filter on.
The `queries_emis` file includes 10 000 queries for the exact match in set filter alongside the computed expected
results. This file is downloaded at prepare time. When `ingest_percentage` is not 100 the pre-computed expected results
are not used, falling back to a brute-force computation of the closest matches that were ingested for the same query
vectors.

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

### Challenge structure

The `index-and-search` challenge (default) includes these phases:

- **`setup`** - recreate the index and wait for green health
- **`index`** - bulk ingest, refresh, and wait for merges
- **`search`** - kNN search (1-client and multi-client) before force-merge
- **`force-merge`** - force-merge, refresh, wait for merges; skipped with `include_force_merge=false`
- **`search-after-force-merge`** - same search operations repeated after force-merge

Example: re-run searches only against an existing index:
```bash
esrally race --track-path=. --include-filter-tags=search-after-force-merge ...
```

### Parameters

This track accepts the following parameters with `--track-params`:

**Indexing**
- `bulk_size` (default: 500): Documents per bulk request.
- `bulk_indexing_clients` (default: 1): Number of bulk indexing clients.
- `bulk_warmup` (default: 40): Warmup time in seconds for the initial bulk phase.
- `corpora` (default: `"arxiv-for-fanns-large"`): Override the corpus name.
- `index_settings` (default: `{}`): Extra index settings.
- `index_mode`: If set, passed as `index.mode`.
- `ingest_percentage` (default: 100): Percentage of the corpus to ingest. When set below 100, the recall operation computes ground truth dynamically via exact search against the indexed subset rather than using the pre-computed `ids` from the queries file.
- `number_of_replicas` (default: 0)
- `number_of_shards` (default: 1)
- `post_ingest_sleep` (default: false): Whether to pause after each ingest phase.
- `post_ingest_sleep_duration` (default: 30): Sleep duration in seconds.

**Index mapping**
- `vector_index_element_type` (default: not set): Element type for the dense vector field.
- `vector_index_type` (default: `"bbq_disk"`): Index type for the dense vector field.
- `vector_index_on_disk_rescore` (default: true): Whether to rescore on disk.
- `vector_similarity` (default: `"cosine"`): Similarity metric.
- `enable_experimental_features` (default: true): Enables `index.dense_vector.experimental_features`.
- `hnsw_m` (default: not set): HNSW `m` parameter.
- `hnsw_ef_construction` (default: not set): HNSW `ef_construction` parameter.
- `bits` (default: not set): Quantization bits (for BBQ variants).

**Force-merge**
- `include_force_merge` (default: false): Whether to run the force-merge phase.
- `force_merge_timeout` (default: 7200): Maximum seconds for force-merge.
- `max_num_segments` (default: 1): Target segment count for force-merge.

**Search**
- `knn_k` (default: 100): `k` for kNN search.
- `knn_num_candidates` (default: 256): `num_candidates` for kNN search.
- `oversample` (default: not set): Oversampling factor for `rescore_vector`.
- `search_request_timeout` (default: 600): Request timeout in seconds for kNN search.
- `recall_request_timeout` (default: 600): Request timeout in seconds for the recall operation.
- `warmup_iterations` (default: 1000): Warmup iterations per search client.
- `iterations` (default: 10000): Measurement iterations per search client.
- `search_clients` (default: 8): Number of clients for the multi-client search steps.

**Queries**
- `queries_file` (default: `"queries_emis.json.zst"`): Name of the queries file to download and use.
- `base_url` (default: `"https://rally-tracks.elastic.co/arxiv_for_fanns"`): Base URL for downloading the queries file.

[dataset_paper]: https://arxiv.org/html/2507.21989v1

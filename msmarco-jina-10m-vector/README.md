## msmarco-jina-10m-vector track

This track benchmarks the first 10M passages from the [MSMARCO (passage, version 2)](https://ir-datasets.com/msmarco-passage-v2.html) corpus embedded into 1024-dimensional, L2-normalized vectors with the [Jina v5-small](https://jina.ai/) embedding model.

Documents contain `docid` and `emb` only (vectors-only mapping, no title or text). Recall is measured against vector top-100 ground truth per query, not human qrels.

Corpus shards are hosted at `https://rally-tracks.elastic.co/msmarco-jina-10m-vector`. Query files ship with the track.

### Example document

```json
{"docid": "00_587", "emb": [0.01, -0.02, ...]}
```

### Queries

**Throughput queries** — `queries.json.bz2`: 10,000 lines, each a JSON array of 1024 floats.

**Recall queries** — `queries-recall-10k.json.bz2`: 10,000 lines, each:

```json
{"query_id": "121352", "emb": [...], "ids": [["1734867", 0.704659], ...]}
```

Ground truth depth is 100 (recall@10, @50, @100 only).

### Challenge: index-and-search

1. Bulk-index the corpus (10M documents by default)
2. Wait for background merges to finish
3. Run the configured search and recall operation matrix (multi-segment index)
4. Force-merge to a single segment per shard (non-serverless only, by default)
5. Run the same search and recall matrix again (single-segment index)

Pure vector search only — no metadata filters, no hybrid/BM25.

### Serverless

The track can run on Elasticsearch Serverless with limitations:

- **Force-merge is disabled by default** on serverless (`include_force_merge` defaults to `false`). The pre/post force-merge comparison is skipped; ingest, search, and recall still run.
- **Index settings** such as `number_of_shards` and `number_of_replicas` are omitted on serverless unless `include_non_serverless_index_settings` is set or `serverless_operator` is `true`.
- Not all `vector_index_type` values may be available on serverless; check your project capabilities.

On a **hosted (non-serverless) Elasticsearch** cluster, force-merge runs by default.

### Parameters

Configure with Rally 0.8.0+ via `--track-params` or a params file.

**Index mapping**

- `vector_index_type` (default: `bbq_hnsw`)
- `vector_index_element_type` (default: `float`)
- `hnsw_m` (default: unset)
- `hnsw_ef_construction` (default: unset)
- `number_of_shards` (default: `1`; omitted on serverless by default)
- `number_of_replicas` (default: `0`; omitted on serverless by default)
- `enable_experimental_features` (default: `false`)
- `include_non_serverless_index_settings` (default: `true` on non-serverless, `false` on serverless)

**Ingest**

- `corpora` (default: `["msmarco-jina-10m"]`)
- `bulk_size` (default: `500`)
- `bulk_indexing_clients` (default: `5`)
- `bulk_warmup` (default: `40`)
- `ingest_percentage` (default: `100`)

**Search / recall**

- `search_ops` (default: `[[null, null], [10, 15], [10, 50], [10, 100], [50, 100], [100, 150]]`): list of `[k, num_candidates]` pairs. Use JSON `null` to omit a value and let Elasticsearch apply its default for that parameter.
- `iterations` (default: `10000`)
- `warmup_iterations` (default: `1000`)
- `search_clients` (default: `8`)

In `--track-params`, use JSON **`null`** to omit `k` or `num_candidates`. Rally operation names use the label **`default`** for omitted slots (for example `knn-recall-default-default`, `knn-recall-10-default`, `knn-recall-default-20`).

| `search_ops` entry | Operation suffix | Meaning |
|--------------------|------------------|---------|
| `[null, null]` | `default-default` | ES defaults for both |
| `[10, null]` | `10-default` | `k=10`, ES default for `num_candidates` |
| `[null, 20]` | `default-20` | ES default for `k`, `num_candidates=20` |
| `[10, 50]` | `10-50` | both explicit |

Recall results include `effective_k` (the K actually used). When `k` was omitted, `effective_k` comes from the search response; when `k` was set, `effective_k` equals `k`.

**Force merge** (non-serverless by default)

- `force_merge_max_num_segments` (default: `1`)
- `force_merge_timeout` (default: `7200`)
- `include_force_merge` (default: `true` on non-serverless, `false` on serverless)

### Example runs

```console
esrally race --track-path=msmarco-jina-10m-vector --challenge=index-and-search
```

Against an existing cluster:

```console
esrally race \
  --pipeline=benchmark-only \
  --track-path=msmarco-jina-10m-vector \
  --challenge=index-and-search \
  --target-hosts=HOST:443 \
  --client-options="use_ssl:true,verify_certs:true,api_key:API_KEY"
```

Custom index type and search matrix:

```console
esrally race --track-path=msmarco-jina-10m-vector --challenge=index-and-search \
  --track-params='{"vector_index_type":"int8_hnsw","search_ops":[[10,100],[100,150]]}'
```

Only ES-default kNN parameters:

```console
esrally race --track-path=msmarco-jina-10m-vector \
  --track-params='{"search_ops":[[null,null],[10,null],[10,100]]}'
```

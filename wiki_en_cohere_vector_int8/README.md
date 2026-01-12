## Cohere Wikipedia int8 vector track

This track benchmarks vector search using the [Cohere/wikipedia-2023-11-embed-multilingual-v3-int8-binary](https://huggingface.co/datasets/Cohere/wikipedia-2023-11-embed-multilingual-v3-int8-binary) dataset containing English Wikipedia articles with int8 embeddings generated using Cohere's `embed-multilingual-v3` model.

### Dataset Overview

- **Documents**: ~41.5 million English Wikipedia articles
- **Vector dimensions**: 1024
- **Element type**: `byte` (int8 vectors stored as base64-encoded strings)
- **Similarity metric**: `max_inner_product`
- **Queries**: 1,000 query vectors
- **True neighbors**: Top 1,000 nearest neighbors per query for recall calculation

### Example Document

```json
{
  "docid": "doc123",
  "title": "Example Article",
  "text": "This is the article content...",
  "emb": "base64_encoded_byte_vector_1024_dimensions"
}
```

The `emb` field contains a base64-encoded byte array representing the 1024-dimensional int8 vector.

### Mapping Types

This track supports three mapping types, selectable via the `mapping_type` parameter:

- `vectors-only`: Only the vector field (`emb`)
- `vectors-only-with-docid` (default): Vector field plus `docid` keyword field
- `vectors-with-text`: Vector field plus `docid`, `title`, and `text` fields

### Parameters

This track accepts the following parameters with Rally 0.8.0+ using `--track-params`:

#### Indexing Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `initial_indexing_bulk_size` | `500` | Bulk request size |
| `initial_indexing_bulk_warmup` | `40` | Warmup time in seconds |
| `initial_indexing_bulk_indexing_clients` | `5` | Number of indexing clients |
| `initial_indexing_ingest_percentage` | `100` | Percentage of corpus to ingest |

#### Post-Ingest Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `post_ingest_sleep` | `false` | Whether to pause after ingest |
| `post_ingest_sleep_duration` | `30` | Sleep duration in seconds |

#### Search Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `standalone_search_clients` | `8` | Number of search clients for multi-client tests |
| `standalone_search_iterations` | `10000` | Iterations per search operation |
| `search_ops` | `[[10, 20], [10, 50], [10, 100], [100, 120], [100, 200], [100, 500]]` | Vector search operations as `[k, num_candidates]` tuples |

#### Index Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `vector_index_type` | `"hnsw"` | Vector index type (`hnsw`, `flat`, etc.) |
| `mapping_type` | `"vectors-only-with-docid"` | Index mapping variant |
| `number_of_shards` | `1` | Number of index shards |
| `number_of_replicas` | `0` | Number of index replicas |
| `preload_pagecache` | (unset) | Whether to preload vector files to page cache |
| `index_settings` | `{}` | Additional index settings |

### Example Usage

Run with default settings:
```bash
esrally race --track=wiki_en_cohere_vector_int8 --target-hosts=localhost:9200
```

Run with custom parameters:
```bash
esrally race --track=wiki_en_cohere_vector_int8 \
  --target-hosts=localhost:9200 \
  --track-params="initial_indexing_bulk_indexing_clients:8,vector_index_type:'hnsw'"
```

Run with vectors-only mapping:
```bash
esrally race --track=wiki_en_cohere_vector_int8 \
  --target-hosts=localhost:9200 \
  --track-params="mapping_type:'vectors-only'"
```

### Notes

- **Byte vectors**: This track uses `element_type: byte` in the dense_vector mapping since vectors are pre-quantized to int8. The default `vector_index_type` is `hnsw` (not `int8_hnsw`) since additional quantization is not needed.
- **No oversample/rescore**: Quantization rescoring is not currently supported for byte element type vectors, so the `search_ops` parameter only accepts `[k, num_candidates]` tuples (no oversample parameter).
- **Base64 encoding**: All vectors in the corpus are base64-encoded, which reduces storage and transfer size compared to float arrays.

### License

This dataset uses the same license as the original Cohere Wikipedia dataset. Please refer to the [Hugging Face dataset page](https://huggingface.co/datasets/Cohere/wikipedia-2023-11-embed-multilingual-v3-int8-binary) for licensing details.

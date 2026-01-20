## OpenAI vector track

This track benchmarks the [NQ dataset](https://huggingface.co/datasets/BeIR/nq) enriched with embeddings generated using OpenAI's [`text-embedding-ada-002` model](https://openai.com/blog/new-and-improved-embedding-model).

### Generating the document dataset

To rebuild the document dataset:

1. Install Python dependencies listed in `_tools/requirements.txt`
2. Download the raw corpus dataset [from here](https://rally-tracks.elastic.co/openai_vector/raw_data/corpus/nq_openai-text-embedding-ada-002_corpus_dataset.arrow)
3. Run `./_tools/parse_documents.py <raw_corpus_dataset_path>`

This will build the document dataset files in the `openai-documents` directory.

### Example Document

```json
{
  "docid": "doc0",
  "title": "Minority interest",
  "text": "In accounting, minority interest (or non-controlling interest) is the portion of a subsidiary corporation's stock that is not owned by the parent corporation. The magnitude of the minority interest in the subsidiary company is generally less than 50% of outstanding shares, or the corporation would generally cease to be a subsidiary of the parent.[1]",
  "emb": [-0.01128644309937954, -0.02616020105779171, 0.012801663018763065, ...]
}
```

### Generating the queries

To rebuild the `queries.json.bz2` file:

1. Install Python dependencies listed in `_tools/requirements.txt`
2. Download the raw queries dataset [from here](https://rally-tracks.elastic.co/openai_vector/raw_data/queries/nq_openai-text-embedding-ada-002_queries_dataset.arrow)
3. Run `./_tools/parse_queries.py <raw_queries_dataset_path>`

### Parameters

This track accepts the following parameters with Rally 0.8.0+ using `--track-params`:

- initial_indexing_corpora (default: openai_initial_indexing_floats) : Use "openai_initial_indexing_base64"  for base64 encoded vectors. 
- initial_indexing_bulk_size (default: 500)
- initial_indexing_bulk_warmup (default: 40)
- initial_indexing_bulk_indexing_clients (default: 5)
- initial_indexing_ingest_percentage (default: 100)
- parallel_indexing_corpora (default: openai_parallel_indexing_floats) : Use "openai_parallel_indexing_base64" for base64 encoded vectors.
- parallel_indexing_bulk_size (default: 500)
- parallel_indexing_bulk_clients (default: 1)
- parallel_indexing_ingest_percentage (default: 100)
- parallel_indexing_time_period (default: 1800)
- parallel_indexing_bulk_target_throughput (default: 1)
- parallel_indexing_search_clients (default: 3)
- parallel_indexing_search_target_throughput (default: 100)
- post_ingest_sleep (default: false): Whether to pause after ingest and prior to subsequent operations.
- post_ingest_sleep_duration (default: 30): Sleep duration in seconds.
- standalone_search_clients (default: 8)
- standalone_search_iterations (default: 10000)
- vector_index_type (default: "hnsw"): The index kind for storing the vectors.
- element_type (default: "float"): Sets the dense_vector element type.
- search_ops (default: [[10, 20, 0], [10, 20, 1], [10, 20, 2], [10, 50, 1], [10, 50, 2], [10, 100, 1], [100, 120, 1], [100, 120, 2], [100, 200, 1], [100, 200, 2], [100, 500, 1], [100, 500, 2]]): The vector search operations, formattied [k, num_candidates, oversample], where `oversample` indicates the ratio of extra `k` to gather and then rescore.

### License

We use the same license for the data as the original data: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

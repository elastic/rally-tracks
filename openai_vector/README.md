## OpenAI vector track

This track benchmarks the [NQ dataset](https://huggingface.co/datasets/BeIR/nq) enriched with embeddings generated using OpenAI's [`text-embedding-ada-002` model](https://openai.com/blog/new-and-improved-embedding-model).

TODO: Describe required cluster size

### Generating the document dataset

TODO: Where to download the dataset from publicly?

### Example Document

TODO: Complete section

### Generating the queries

TODO: Complete section

### Parameters

This track accepts the following parameters with Rally 0.8.0+ using `--track-params`:

 - bulk_size (default: 500)
 - bulk_indexing_clients (default: 5)
 - build_warmup (default: 40)
 - ingest_percentage (default: 100)
 - index_settings {default: {}}
 - number_of_shards (default : 1)
 - number_of_replicas (default: 0)
 - post_ingest_sleep (default: false): Whether to pause after ingest and prior to subsequent operations.
 - post_ingest_sleep_duration (default: 30): Sleep duration in seconds.

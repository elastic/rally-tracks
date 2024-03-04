## Cohere msmarco-v2/embed-english-v3 vector track

This track benchmarks the dataset from [Cohere/msmarco-v2-embed-english-v3](https://huggingface.co/datasets/Cohere/msmarco-v2-embed-english-v3).

Given the size of this dataset 138.3M documents with 1024 dimension vectors you
need a cluster with at least 60GB of total RAM available to run performant HNSW queries.

### Generating the document dataset

To rebuild the dataset run the following commands, **warning** this takes at least 2.7TB of free disk space:

```console
$ cd cohere_v3_vector
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -r _tools/requirements.txt
$ python _tools/parse_documents.py

# Create a test file for each page of documents
$ for file in cohere-documents-*; do
  head -n 1000 $file > "${file%.*}-1k.json"
done

# Zip each document file for uploading
$ for file in cohere-documents-*; do
  pv $file | bzip2 -k >> $file.bz2
done
$ ls -1 cohere-documents-* > files.txt
```

This will build 47 `cohere-documents-XX.json` file for the entire dataset of 138.3M documents and then bzip then. Note that this script depends on the libraries listed `_tools/requirements.txt` to run and it takes a few hours to download and parse all the documents.
### Example Document

```json
{
  "docid": "00_0",
  "title": "0-60 Times - 0-60 | 0 to 60 Times & 1/4 Mile Times | Zero to 60 Car Reviews",
  "text": "0-60 Times - 0-60 | 0 to 60 Times & 1/4 Mile Times | Zero to 60 Car Reviews.",
  "emb": [0.00507354736328125, 0.01519775390625, -0.002109527587890625, ...]
}
```

### Generating the queries

The `queries.json` can be rebuilt using the `_tools/parse_queries.py`, this will stream a partial training dataset from hugging face, call the Cohere embed API for each sample, and then store the embeddings in `queries.json`.

You will need a production API key from (Cohere)[https://dashboard.cohere.com/api-keys], as the trial keys are heavily rate-limited:

```console
$ export COHERE_API_KEY='abcdefghijklmnopqrstuvwxyz'
$ python _tools/parse_queries.py
```

### Parameters

This track accepts the following parameters with Rally 0.8.0+ using `--track-params`:

 - `initial_indexing_bulk_indexing_clients` (default: 5)
 - `initial_indexing_ingest_percentage` (default: 100)
 - `initial_indexing_bulk_size` (default: 500)
 - `initial_indexing_bulk_warmup` (default: 40)
 - `number_of_shards` (default: 1)
 - `number_of_replicas` (default: 0)
 - `parallel_indexing_bulk_clients` (default: 1)
 - `parallel_indexing_bulk_target_throughput` (default: 1)
 - `parallel_indexing_time_period` (default: 1800)
 - `parallel_indexing_search_clients` (default: 3)
 - `parallel_indexing_search_target_throughput` (default: 100)
 - `post_ingest_sleep` (default: false): Whether to pause after ingest and prior to subsequent operations.
 - `post_ingest_sleep_duration` (default: 30): Sleep duration in seconds.
 - `standalone_search_iterations` (default: 10000)
 - `vector_index_type` (default: "int8_hnsw"): The index kind for storing the vectors.

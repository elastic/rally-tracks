## msmarco-v2 vector track

This track benchmarks the dataset from [Cohere/msmarco-v2-embed-english-v3](https://huggingface.co/datasets/Cohere/msmarco-v2-embed-english-v3).
The corpus contains the original 138M passages of the [MSMARCO (passage, version 2)](https://ir-datasets.com/msmarco-passage-v2.html) corpus embedded
into 1024 dimensional vectors with the [Cohere `embed-english-v3.0` model](https://cohere.com/blog/introducing-embed-v3).

### Generating the document dataset

To rebuild the dataset run the following commands, **warning** this takes at least 2.7TB of free disk space:

```console
$ cd msmarco-v2-vector
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
  bzip2 -k $file
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

The `queries.json` can be rebuilt using `_tools/parse_queries.py -t`, this will load the msmarco v2 passages queries dataset, and then call the Cohere embed API for each query, and store the embeddings in `queries.json`.
This will take a very long time, maybe grab a ☕️ ?

You will need a production API key from [Cohere](https://dashboard.cohere.com/api-keys), as the trial keys are heavily rate-limited:

```console
$ export COHERE_API_KEY='abcdefghijklmnopqrstuvwxyz'
$ python _tools/parse_queries.py -t
```

### Generating the queries for the recall operation

The `queries-recall.json` can be rebuilt using `_tools/parse_queries.py -r`, this will load the msmarco v2 passages test queries, and then call the Cohere embed API for each query, store the embeddings in `queries-recall.json` as well as the true top 1000 for each query computed with brute force.
For the relevance metrics, the `qrels.tsv` file contains annotations for all the queries listed in `queries.json`. This file is copied from the original training data available at [msmarco-passage-v2/trec-dl-2022/judged](https://ir-datasets.com/msmarco-passage-v2.html#msmarco-passage-v2).

```console
$ export COHERE_API_KEY='abcdefghijklmnopqrstuvwxyz'
$ python _tools/parse_queries.py -r
```

### Parameters

This track accepts the following parameters with Rally 0.8.0+ using `--track-params`:

 - `aggressive_merge_policy` (default: false): Whether to apply a more aggressive merge strategy.
 - `index_refresh_interval` (default: unset): The index refresh interval.
 - `initial_indexing_bulk_indexing_clients` (default: 5)
 - `initial_indexing_ingest_percentage` (default: 100)
 - `initial_indexing_bulk_size` (default: 500)
 - `initial_indexing_bulk_warmup` (default: 40)
 - `number_of_shards` (default: 1)
 - `number_of_replicas` (default: 0)
 - `parallel_indexing_bulk_clients` (default: 1)
 - `parallel_indexing_bulk_target_throughput` (default: 1)
 - `parallel_indexing_search_clients` (default: 3)
 - `parallel_indexing_search_target_throughput` (default: 100)
 - `post_ingest_sleep` (default: false): Whether to pause after ingest and prior to subsequent operations.
 - `post_ingest_sleep_duration` (default: 30): Sleep duration in seconds.
 - `search_ops` (default: [(10, 20, 0), (10, 20, 20), (10, 50, 0), (10, 50, 20), (10, 100, 0), (10, 100, 20), (10, 200, 0), (10, 200, 20), (10, 500, 0), (10, 500, 20), (10, 1000, 0), (10, 1000, 20), (100, 120, 0), (100, 120, 120), (100, 200, 0), (100, 200, 120), (100, 500, 0), (100, 500, 120), (100, 1000, 0), (100, 1000, 120)]): The search and recall operations to run (k, ef_search, num_rescore).
 - `standalone_search_iterations` (default: 10000)
 - `vector_index_type` (default: "int8_hnsw"): The index kind for storing the vectors.

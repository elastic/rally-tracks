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

The `queries.json` can be rebuilt using the `_tools/parse_queries.py`, this will load the msmarco v2 passages queries dataset, and then call the Cohere embed API for each query, and store the embeddings in `queries.json`.
This will take a very long time, maybe grab a ☕️ ?

You will need a production API key from [Cohere](https://dashboard.cohere.com/api-keys), as the trial keys are heavily rate-limited:

```console
$ export COHERE_API_KEY='abcdefghijklmnopqrstuvwxyz'
$ python _tools/parse_queries.py
```

Given the size of the corpus, the true top N values used for recall operations have been approximated offline for each query as follows:
```
{
    "size": 100,
    "knn": {
        "field": "emb", 
        "query_vector": query['emb'],
        "k": 10000,
        "num_candidates": 10000
    },
    "rescore": {
        "window_size": 10000,
        "query": {
            "query_weight": 0,
                "rescore_query": {
                    "script_score": {
                        "query": {
                            "match_all": {}
                        },
                    "script": { 
                        "source": "double value = dotProduct(params.query_vector, 'emb'); return sigmoid(1, Math.E, -value);",
                        "params": {
                            "query_vector": vec
                        }
                    }
                }
            }
        }
    }
}
```
This means that the computed recall is measured against the system's best possible approximate neighbor run rather than the actual top N.

For the relevance metrics, the `qrels.tsv` file contains annotations for all the queries listed in `queries.json`. This file is generated from the original training data available at [ir_datasets/msmarco_passage_v2](https://ir-datasets.com/msmarco-passage-v2.html#msmarco-passage-v2/train).

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
 - `index_refresh_interval` (default: unset): The index refresh interval.
 - `aggressive_merge_policy` (default: false): Whether to apply a more aggressive merge strategy.

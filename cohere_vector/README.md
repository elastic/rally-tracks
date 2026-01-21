## Cohere vector track

This track benchmarks the dataset from [Cohere/miracl-en-corpus-22-12](https://huggingface.co/datasets/Cohere/miracl-en-corpus-22-12).

Given the size of this dataset 32.8M documents with 768 dimension vectors you
need a cluster with at least 103GB of total RAM available to run performant HNSW queries.

### Generating the document dataset

To rebuild the dataset run the following commands:

```shell
$ python _tools/parse_documents.py
# Create a test file for each page of documents
$ for file in cohere-documents-*; do
  head -n 1000 $file > "${file%.*}-1k.json"
done
# Zip each document file for uploading
$ for file in cohere-documents-*; do
  pv $file | bzip2 -k >> $file.bz2
done
```

This will build 11 `cohere-documents-XX.json` file for the entire dataset of 32.8M documents and then bzip then. Note that this script depends on the libraries listed `_tools/requirements.txt` to run and it takes a few hours to download and parse all the documents.
### Example Document

```json
{
  "docid": "31958810#2",
  "title": "Daybehavior",
  "text": "During 1998 and 1999 they, recorded their follow-up album with Kevin Petri, engineer on Massive Attack's debut album \"Blue Lines\" (1991). NONS, dealing with financial problems, went into bankruptcy 99 and the album was locked from being released. The band in despair decided to take a break and Arell moved to Thailand.",
  "emb": [0.3961234986782074, 0.20130762457847595, 0.45026177167892456, ...]
}
```

### Generating the queries

The `queries.json` can be rebuilt using the `_tools/parse_queries.py`, this will load the queries dataset from hugging face and will output the result to the `queries.json` file.

### Parameters

This track accepts the following parameters with Rally 0.8.0+ using `--track-params`:

 - base_url (default: `https://rally-tracks.elastic.co/cohere-miracl-en-corpus-22-12`): Specifies the bucket path from where to download the data set.
 - initial_indexing_bulk_indexing_clients (default: 5)
 - initial_indexing_ingest_percentage (default: 100)
 - initial_indexing_bulk_size (default: 500)
 - initial_indexing_bulk_warmup (default: 40)
 - number_of_shards (default: 1)
 - number_of_replicas (default: 0)
 - parallel_indexing_bulk_clients (default: 1)
 - parallel_indexing_bulk_target_throughput (default: 1)
 - parallel_indexing_time_period (default: 1800)
 - parallel_indexing_search_clients (default: 3)
 - parallel_indexing_search_target_throughput (default: 100)
 - post_ingest_sleep (default: false): Whether to pause after ingest and prior to subsequent operations.
 - post_ingest_sleep_duration (default: 30): Sleep duration in seconds.
 - standalone_search_iterations (default: 10000)
 - vector_index_type (default: "hnsw"): The index kind for storing the vectors.
 - vector_index_element_type (default: "float"): Sets the dense_vector element type.

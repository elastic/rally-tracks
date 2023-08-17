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

This will build 11 `cohere-documents-XX.json` filse for the entire dataset of 32.8M documents and then bzip then. Note that this script depends on the libraries listed `_tools/requirements.txt` to run and it takes a few hours to download and parse all the documents. This script will normalize the embeddings vector to be unit-length so that they can be indexed in an elasticsearch index.

### Example Document

```json
{
  "docid": "31958810#2",
  "title": "Daybehavior",
  "text": "During 1998 and 1999 they, recorded their follow-up album with Kevin Petri, engineer on Massive Attack's debut album \"Blue Lines\" (1991). NONS, dealing with financial problems, went into bankruptcy 99 and the album was locked from being released. The band in despair decided to take a break and Arell moved to Thailand.",
  "emb": [0.027735009072141308, 0.014094767951423247, 0.03152555797377242, ...]
}
```

### Generating the queries

The `queries.json` can be rebuilt using the `_tools/parse_queries.py`, this will load the queries dataset from hugging face and normalize the vectors outputing the result to the `queries.json` file.

### Parameters

This track accepts the following parameters with Rally 0.8.0+ using `--track-params`:

 - bulk_size (default: 500)
 - bulk_indexing_clients (default: 5)
 - build_warmup (default: 40)
 - ingest_percentage (default: 100)
 - index_settings {default: {}}
 - number_of_shards (default : 1)
 - number_of_replicas (default: 0)

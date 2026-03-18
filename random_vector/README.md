# Random Vector Track

This track is intended for benchmarking filtered vector search using randomly generated vectors in a **multi-partition** setup.
By default, it uses the `bbq_flat` `vector_index_type` to evaluate the performance of brute-force search with partition ID-based filtering.

The `paragraph_size` parameter determines how many random vectors are indexed per document.

* If `paragraph_size` is set to `1` (the default), each document contains a single top-level random vector.
* If `paragraph_size` is greater than `1`, that number of random vectors is indexed as nested fields within each document.

## Multi-Partition Model

Partitions are organized into three tiers with configurable counts:

* **Small partitions** (`small_partitions`, default: 100): 1,000–10,000 documents each
* **Medium partitions** (`medium_partitions`, default: 20): 10,000–100,000 documents each
* **Large partitions** (`large_partitions`, default: 5): 100,000–1,000,000 documents each

The distribution follows a realistic pattern: many small partitions, fewer medium, and fewest large.

Each partition's exact document count is determined by a seeded RNG (`partition_seed`, default: 42), ensuring reproducible runs. During indexing, documents are assigned to partitions via weighted random sampling proportional to each partition's target size.

The index is sorted by `partition_id` and documents are routed by `partition_id`, keeping each partition's data co-located.

## Indexing

Indexing runs in one of two modes, depending on whether `index_target_throughput` is specified.
The track launches `index_clients` parallel clients. Each client sends `index_iterations` bulk requests, with each request containing `index_bulk_size` documents.

The total number of documents indexed is:
`index_clients` × `index_iterations` × `index_bulk_size`

* If `index_target_throughput` is set, each client will send bulk operations at a rate of:
  `index_target_throughput` ÷ `index_clients` bulk requests per second.
* If `index_target_throughput` is not set, each client will send bulk operations as fast as possible.

### Document content and index layout

Each document indexed includes:

* A random vector with `dims` dimensions.
* A partition ID assigned via weighted random selection.

The index is sorted by partition ID and documents are routed by partition ID.
This ensures that vectors from the same partition are stored close together, improving the efficiency of filtered searches.

## Search Operations

Search tasks are broken up by partition tier to separately measure QPS and latency for small, medium, and large partitions:

* `small-partition-search`: Queries only small-tier partitions
* `medium-partition-search`: Queries only medium-tier partitions
* `large-partition-search`: Queries only large-tier partitions

Each search phase filters by a randomly chosen partition ID within the tier and scores against a random query vector.

## Nightly Benchmarking

For nightly runs, use the following recommended parameters:

```
--track-params="dims:1024,vector_index_type:bbq_flat"
--track-params="dims:1024,vector_index_type:bbq_disk"
```

Run both `bbq_flat` and `bbq_disk` to capture performance on both index types.

### Parameters

This track accepts the following parameters with Rally 0.8.0+ using `--track-params`:

 - number_of_shards (default: 1)
 - number_of_replicas (default: 0)
 - vector_index_type (default: bbq_flat)
 - paragraph_size (default: 1)
 - index_target_throughput (default: undefined)
 - index_clients (default: 1)
 - index_iterations (default: 1000)
 - index_bulk_size (default: 1000)
 - search_iterations (default: 10000)
 - search_clients (default: 8)
 - dims (default: 128): Number of dimensions for the random vectors. Use 1024 for nightly runs.
 - small_partitions (default: 100): Number of small partitions (1k–10k docs each).
 - medium_partitions (default: 20): Number of medium partitions (10k–100k docs each).
 - large_partitions (default: 5): Number of large partitions (100k–1M docs each).
 - partition_seed (default: 42): Seed for deterministic partition size assignment.
 - rescore_oversample (default: 0)
 - vector_index_element_type (default: "float"): Sets the dense_vector element type.
 - enable_experimental_features (default: false): Enables experimental dense vector features that may break backward compatibility.

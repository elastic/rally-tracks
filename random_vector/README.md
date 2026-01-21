# Random Vector Track

This track is intended for benchmarking filtered vector search using randomly generated vectors.
By default, it uses the `bbq_flat` `vector_index_type` to evaluate the performance of brute-force search with partition ID-based filtering.

The `paragraph_size` parameter determines how many random vectors are indexed per document.

* If `paragraph_size` is set to `1` (the default), each document contains a single top-level random vector.
* If `paragraph_size` is greater than `1`, that number of random vectors is indexed as nested fields within each document.

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
* A randomly assigned partition ID.

The index is sorted by partition ID. 
This ensures that vectors from the same partition are stored close together, improving the efficiency of filtered searches.

## Search Operations

Search operations involve filtering by a random partition ID and scoring against a random query vector. 
These operations are executed against the index using various DSL flavors, including script score and knn section.

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
 - search_iterations (default: 1000)
 - search_clients (default: 8)
 - dims (default: 128)
 - partitions (default: 1000)
 - rescore_oversample (default: 0)
 - vector_index_element_type (default: "float"): Sets the dense_vector element type.

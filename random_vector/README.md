# Random Vector Track

This track is designed for benchmarking filtered search on random vectors.

By default, the `flat` vector_index_type is utilized to evaluate the performance
of brute force search over vectors filtered by a partition ID.

## Indexing

The track performs indexing in one of two modes, depending on whether `index_target_throughput` is defined:

* **Without `index_target_throughput`**
  If `index_target_throughput` is not set, the track launches `index_clients` parallel clients. Each client executes `index_iterations` bulk requests, with each request containing `index_bulk_size` documents.
  The total number of documents indexed is:
  `index_clients` × `index_iterations` × `index_bulk_size`

* **With `index_target_throughput`**
  If `index_target_throughput` is set, the track performs `index_iterations` bulk requests, each of size `index_bulk_size`, while aiming to sustain the target throughput (`index_target_throughput`) in documents per second.
  The total number of documents indexed is:
  `index_iterations` × `index_bulk_size`

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
 - vector_index_type (default: flat)
 - index_target_throughput (default: undefined)
 - index_clients (default: 1)
 - index_iterations (default: 1000)
 - index_bulk_size (default: 1000)
 - search_iterations (default: 1000)
 - search_clients (default: 8)
 - dims (default: 128)
 - partitions (default: 1000)
 - use_synthetic_source (default: false)
 - routing (default: false)
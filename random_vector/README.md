# Random Vector Track

This track is designed for benchmarking filtered search on random vectors.

By default, the `flat` vector_index_type is utilized to evaluate the performance
of brute force search over vectors filtered by a partition ID.

## Indexing

To begin indexing, the track initiates `index_clients` clients, each executing `index_iterations` bulk operations of size `index_bulk_size`. 
Consequently, the total number of documents indexed by the track is calculated as follows: `index_clients` * `index_iterations` * `index_bulk_size`.

Each document in the bulk is assigned a random vector of dimensions `dims` and a random partition ID.
The resulting index is sorted on the partition id. This helps make sure vectors are close together when we do filtered searches.

## Search Operations

Search operations involve filtering by a random partition ID and scoring against a random query vector. 
These operations are executed against the index using various DSL flavors, including script score and knn section.

### Parameters

This track accepts the following parameters with Rally 0.8.0+ using `--track-params`:

 - number_of_shards (default: 1)
 - number_of_replicas (default: 0)
 - vector_index_type (default: flat)
 - index_clients (default: 1)
 - index_iterations (default: 1000)
 - index_bulk_size (default: 1000)
 - search_iterations (default: 1000)
 - search_clients (default: 8)
 - dims (default: 128)
 - partitions (default: 1000)
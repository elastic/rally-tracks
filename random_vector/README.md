# Random Vector Track

This track is designed for benchmarking filtered search on random vectors.

By default, the flat vector_index_type is utilized to evaluate the performance of brute force search over vectors filtered by a partition ID.

## Index Type Configuration

The track supports creating either an index or datastream based on the `index_type` parameter:
- `index_type: "datastream"` (default) - Creates a data stream
- `index_type: "index"` - Creates a regular index

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

## Challenges

### Default Challenge: `index-and-search`
The standard challenge that creates an index/datastream, indexes documents, and performs search operations.

### Autoscale Challenge: `ingest-search-autoscale`
A specialized challenge that mimics autoscaling behavior with configurable steps and parallel search/indexing operations.

**Autoscaling Parameters:**
- `as_ingest_clients` - Array of client counts for each autoscaling step
- `as_ingest_bulk_size` - Array of bulk sizes for each step
- `as_ingest_target_throughputs` - Array of target throughputs for each step
- `as_ingest_index_iterations` - Array of iteration counts for each step

**Parallel Operation Parameters:**
- `parallel_warmup_time_periods` - Warmup duration for parallel operations
- `parallel_time_periods` - Duration for parallel operations
- `parallel_indexing_clients` - Number of parallel indexing clients
- `parallel_ingest_target_throughputs` - Target throughput for parallel indexing
- `parallel_indexing_bulk_size` - Bulk size for parallel indexing
- `parallel_search_clients` - Number of parallel search clients

## Parameters

This track accepts the following parameters with Rally 0.8.0+ using `--track-params`:

### Basic Parameters
 - number_of_shards (default: 1)
 - number_of_replicas (default: 0)
 - vector_index_type (default: flat)
 - index_type (default: datastream) - Choose between "index" or "datastream"
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

### Autoscaling Parameters (for ingest-search-autoscale challenge)
 - as_ingest_clients (default: [5,20,5]) - Array of client counts per step
 - as_ingest_bulk_size (default: [100,100,100]) - Array of bulk sizes per step
 - as_ingest_target_throughputs (default: [10,50,10]) - Array of target throughputs per step
 - as_ingest_index_iterations (default: [1000,2000,1500]) - Array of iteration counts per step

### Parallel Operation Parameters (for ingest-search-autoscale challenge)
 - parallel_warmup_time_periods (default: 10) - Warmup duration in time periods
 - parallel_time_periods (default: 10) - Operation duration in time periods
 - parallel_indexing_clients (default: 1) - Number of parallel indexing clients
 - parallel_ingest_target_throughputs (default: 1) - Target throughput for parallel indexing
 - parallel_indexing_bulk_size (default: 10) - Bulk size for parallel indexing
 - parallel_search_clients (default: 10) - Number of parallel search clients
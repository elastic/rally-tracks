## ELSER Speed Test Track

### Prerequisites
#### Set up ES cloud deployment
Create a deployment which contains an ML node with at least 4GB of memory.

### Parameters
This track accepts the following parameters with Rally 0.8.0+ using `--track-params`:
* `number_of_allocations` (default: 1)
* `threads_per_allocation` (default: 2)
* `queue_capacity` (default: 1024)
* `bulk_size` (default: 100)
* `bulk_indexing_clients` (default: 1)
* `ingest_percentage` (default: 100)


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

### Data Setup
The documents are all of a fixed length input equivalent to 256 Word Piece tokens. They were created by taking words from the BERT vocabulary that tokenize as a single token and generating fixed length inputs from a random selection of single token words.

See `_support/generate_fixed_length_docs.py` and other files in the `_support` folder.
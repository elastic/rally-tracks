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

### Challenges
This rally track includes a challenge for each version of the ELSER model:
* ELSER-V1: ".elser_model_1"
* ELSER-V2 Platform Agnostic: ".elser_model_2"
* ELSER-V2 Platform Specific: ".elser_model_2_linux-x86_64"

There is also a multi-parametric challenge to decrease the number of esbench instances that need to be started to run the track: 
* Multi-Parametric-ELSER-V2-PlatformSpecific: 
    * note that this challenge has different track parameters and defaults
    * Additional Parameters:
      * `pipeline_name` (default: "default-pipeline")
      * `model_id`




### Data Setup
The documents are all of a fixed length input equivalent to 256 Word Piece tokens. They were created by taking words from the BERT vocabulary that tokenize as a single token and generating fixed length inputs from a random selection of single token words.

See `_support/generate_fixed_length_docs.py` and other files in the `_support` folder.
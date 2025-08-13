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
* `ingest_percentage` (default: challenge dependent)

### Challenges
This rally track includes a challenge for each version of the ELSER model:
* ELSER-V1: ".elser_model_1"
* ELSER-V2 Platform Agnostic: ".elser_model_2"
* ELSER-V2 Platform Specific: ".elser_model_2_linux-x86_64"
* ELSER-V2-eis: ".elser-2-elastic"

There are also two multi-parametric challenges to decrease the number of esbench instances that need to be started. These challenges take the same parameters as the other challenges, plus extra ones, but the meaning of the parameters is slightly different: 
* ELSER-Multi-Parametric-Ingest: 
    * Reused Parameters:
      * `number_of_allocations` indicates the maximum number of allocations to test, every number below this and greater than 0 will be tested. 
    * Additional Parameters:
      * `pipeline_name` (default: "default-pipeline")
      * `model_id`
* ELSER-Multi-Doc-Size-Multi-allocations-Parametric-Ingest:

    *Note*: To account for the increased throughput associated with smaller doc sizes, in this challenge the bulk_size is automatically adjusted according to this formula: 512 - doc_size + 25*l_num_allocations, although this formula is not considered to be ideal for this test.

    * `max_number_of_allocations` indicates the maximum number of allocations to test, every number below this and greater than and equal to `min_number_of_allocations` will be tested.
    * `min_number_of_allocations` indicates the minimum number of allocations to test, every number above this less than and equal to `max_number_of_allocations` will be tested.
    * The doc size parameters must be set together to match the available datasets 
      * `min_doc_size` the size of the smallest document to test
      * `max_doc_size` the size of the largest document to test
      * `doc_size_delta` the marginal increase in document size between tests.
    * `pipeline_name` (default: "default-pipeline")
    * `model_id`




### Data Setup
In the `ELSER-V1`, `ELSER-V2`, and `ELSER-V2-PlatformSpecific` challenges, the documents are all of a fixed length input equivalent to 256 Word Piece tokens. The `ELSER-Multi-Doc-Multi-Parametric-Ingest` challenge uses multiple document sets of fixed lengths. See `track.json` for the corpora of document sets available for use.

They were created by taking words from the BERT vocabulary that tokenize as a single token and generating fixed length inputs from a random selection of single token words.

See `_support/generate_fixed_length_docs.py` and other files in the `_support` folder.

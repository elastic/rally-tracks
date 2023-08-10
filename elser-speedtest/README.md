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

### License
Terms and Conditions for using the MS MARCO datasets can be found at https://microsoft.github.io/msmarco/

### Citation
@article{bajaj2016ms,
title={Ms marco: A human generated machine reading comprehension dataset},
author={Bajaj, Payal and Campos, Daniel and Craswell, Nick and Deng, Li and Gao, Jianfeng and Liu, Xiaodong and Majumder, Rangan and McNamara, Andrew and Mitra, Bhaskar and Nguyen, Tri and others},
journal={arXiv preprint arXiv:1611.09268},
year={2016}
}


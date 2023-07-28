## MS MARCO Passage ELSER Track

### Prerequisites
#### Set up ES cloud deployment
Create a deployment which contains an ML node
#### Install Elasticsearch >=8.9 with pip (or manually downlaod ELSER)
Warning: esrally is theoretically not compatible with elasticsearch>8.6.1, but we need it to run this track

`python -m pip install elasticsearch -U`

Alternatively, you can manually download the `.elser_model_1` model (this is a currently a manual step, but can be automated pending the release of an updated python client)


### Parameters
This track accepts the following parameters with Rally 0.8.0+ using `--track-params`:
* `number_of_allocations` (default: 1)
* `threads_per_allocation` (default: 2)
* `queue_capacity` (default: 1024)
* `bulk_size` (default: 5000)
* `bulk_indexing_clients` (default: 8)
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


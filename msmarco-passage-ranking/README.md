## MS MARCO Passage Ranking Track

This track assesses the search performance of the dataset available at [microsoft/MSMARCO-Passage-Ranking](https://github.com/microsoft/MSMARCO-Passage-Ranking).
To compare search performance, the following strategies are employed:
* `bm25`: This is a straightforward strategy that involves indexing the text fields using a standard analyzer and querying using the match query method.
* `text-expansion`: In this strategy, we utilize ELSER v2 to expand both the documents and queries with weighted tokens. It's worth noting that the original dataset has already been augmented with these weighted tokens.
* `hybrid`: The hybrid strategy combines both the bm25 and text-expansion approaches at query time. This is achieved through a simple boolean logic and a query type-specific boost.

It's important to highlight that the text-expansion and hybrid strategies are dependent on a dataset that has undergone query token expansion.

### Example Document

Documents adhere to the [JSON Lines format](https://jsonlines.org/). 
When a single document is pretty printed, it takes the following example format:

<details>
  <summary><i>Example document</i></summary>

```json
{
  "text": " The Manhattan Project and its atomic bomb helped bring an end to World War II. Its legacy of peaceful uses of atomic energy continues to have an impact on history and science.",
  "text_expansion": {
    "1059": 0.421,
    "2001": 0.6255,
    "2020": 0.0634,
    "2088": 0.2231,
    "2109": 0.1628,
    "2134": 0.1978,
    "2137": 0.0752,
    "2149": 0.0402,
    "2162": 1.2239,
    "2203": 1.0947,
    "2224": 0.4831,
    "2231": 0.0336,
    "2259": 0.3049,
    "2373": 0.5267,
    "2381": 0.2278,
    "2390": 0.4375,
    "2393": 0.9349,
    "2458": 0.0597,
    "2462": 1.2176,
    "2485": 0.1358,
    "2506": 0.1082,
    "2510": 0.4909,
    "2565": 0.26,
    "2590": 0.6441,
    "2622": 1.5416,
    "2644": 0.001,
    "2645": 0.2524,
    "2651": 0.3213,
    "2671": 0.6477,
    "2716": 0.5822,
    "2744": 0.0049,
    "2801": 0.0914,
    "2887": 0.2356,
    "2933": 0.0174,
    "2943": 1.2381,
    "2974": 0.3506,
    "3067": 0.0165,
    "3092": 0.6848,
    "3169": 0.102,
    "3171": 0.0551,
    "3260": 0.5757,
    "3271": 0.9628,
    "3278": 0.2852,
    "3288": 0.7182,
    "3303": 0.371,
    "3354": 0.4145,
    "3377": 0.5098,
    "3386": 0.4223,
    "3399": 0.1536,
    "3426": 0.5563,
    "3439": 0.0458,
    "3466": 0.2532,
    "3521": 0.6129,
    "3578": 0.3402,
    "3594": 0.141,
    "3595": 0.4986,
    "3613": 0.0241,
    "3646": 0.1307,
    "3690": 0.2161,
    "3747": 0.1906,
    "3758": 1.109,
    "3796": 0.3924,
    "3800": 0.2509,
    "3826": 0.1882,
    "3874": 0.6584,
    "3882": 0.0039,
    "3910": 0.1751,
    "3928": 0.0887,
    "3934": 0.7201,
    "3947": 0.1091,
    "3987": 0.1195,
    "4105": 0.1117,
    "4204": 0.1082,
    "4254": 0.8048,
    "4255": 0.6086,
    "4337": 0.2569,
    "4471": 0.0905,
    "4483": 0.1586,
    "4517": 1.135,
    "4566": 0.0029,
    "4585": 0.4575,
    "4736": 0.6097,
    "4762": 0.5104,
    "5036": 0.4274,
    "5072": 0.1686,
    "5081": 0.3085,
    "5094": 0.0698,
    "5195": 0.8109,
    "5233": 0.3737,
    "5584": 0.393,
    "5656": 0.2018,
    "5951": 0.3451,
    "5968": 1.5432,
    "6035": 0.2852,
    "6150": 0.0289,
    "6179": 0.2734,
    "6215": 0.586,
    "6245": 0.3791,
    "6344": 0.067,
    "6378": 0.3629,
    "6394": 0.8048,
    "6396": 0.7702,
    "6614": 0.4618,
    "6691": 0.6155,
    "6755": 0.067,
    "6831": 0.1477,
    "6842": 0.3113,
    "7091": 0.3831,
    "7128": 2.0794,
    "7421": 0.2667,
    "7461": 0.3897,
    "8027": 1.3858,
    "8249": 0.2302,
    "8573": 0.9287,
    "8647": 0.2675,
    "8826": 0.2779,
    "9274": 0.1056,
    "9379": 1.347,
    "9433": 0.2998,
    "9472": 0.1719,
    "9593": 1.2129,
    "9714": 0.3149,
    "9767": 0.6102,
    "9881": 0.3185,
    "9915": 0.1669,
    "10585": 0.2247,
    "12498": 0.1686,
    "13298": 0.0029,
    "13353": 0.2034,
    "13787": 0.8748,
    "14247": 0.5506,
    "15699": 0.0383,
    "17669": 0.227,
    "17690": 0.1544,
    "18114": 0.0232,
    "19320": 0.0107,
    "20168": 0.189,
    "20223": 0.4337,
    "21614": 0.5904,
    "25755": 0.5751,
    "28846": 0.1751
  }
}
```
</details>

The `text_expansion` field contains weighted tokens expanded with ELSER v2 from the `text` field.

### Example Query

Queries are structured within a JSON array, where each individual object signifies a unique 'query' and its corresponding expansion achieved through ELSER v2, which is stored pre-computed in the 'query_expansion' field.:

<details>
  <summary><i>Example query object</i></summary>

```json
{
    "query": ")what was the immediate impact of the success of the manhattan project?",
    "query_expansion": {
        "1007": 0.0467,
        "2001": 0.7492,
        "2020": 0.0107,
        "2054": 0.1719,
        "2137": 0.1536,
        "2150": 0.343,
        "2162": 0.1264,
        "2220": 0.3013,
        "2234": 0.1064,
        "2458": 0.3609,
        "2537": 0.2433,
        "2590": 0.4951,
        "2622": 1.6016,
        "2765": 0.2524,
        "2810": 0.0815,
        "2933": 0.0905,
        "3066": 0.1882,
        "3112": 1.6759,
        "3144": 1.1732,
        "3169": 0.2121,
        "3171": 0.5579,
        "3202": 1.0016,
        "3260": 0.3163,
        "3278": 0.234,
        "3303": 0.435,
        "3354": 0.4463,
        "3377": 0.3547,
        "3381": 0.2247,
        "3386": 0.1898,
        "3462": 0.0029,
        "3466": 0.9516,
        "3578": 0.4807,
        "3740": 0.3751,
        "3758": 0.6694,
        "3845": 0.0788,
        "3874": 0.1536,
        "3890": 0.0346,
        "3925": 0.0421,
        "3947": 0.1029,
        "4105": 0.2247,
        "4158": 0.1108,
        "4187": 0.068,
        "4254": 1.4524,
        "4483": 0.6076,
        "4517": 0.9194,
        "4736": 0.1108,
        "4926": 0.0698,
        "4945": 0.4469,
        "5036": 0.2137,
        "5081": 0.3099,
        "5082": 0.1502,
        "5817": 0.241,
        "5951": 0.3374,
        "5968": 0.6883,
        "6035": 0.2263,
        "6186": 0.0402,
        "6215": 0.3206,
        "6234": 1.4936,
        "6256": 0.0058,
        "6344": 0.6223,
        "6378": 0.7315,
        "6396": 0.0523,
        "6580": 0.286,
        "7128": 2.0289,
        "7461": 0.6533,
        "7738": 0.0634,
        "7784": 0.3113,
        "8027": 0.4171,
        "8573": 1.1243,
        "9274": 0.2417,
        "9560": 0.234,
        "9727": 0.2823,
        "9915": 0.1536,
        "10530": 0.1519,
        "10796": 0.1776,
        "12393": 0.0523,
        "14200": 0.1994,
        "14463": 0.4698,
        "15237": 0.0458,
        "16551": 0.1809,
        "16696": 0.2852,
        "17060": 0.0058,
        "20223": 0.5393,
        "20506": 0.2874
    }
}
```
</details>

The `query_expansion` field contains weighted tokens expanded with ELSER v2 from the `query` field.

### Parameters
This track accepts the following parameters with Rally 0.8.0+ using `--track-params`:

* `bulk_size` (default: 5000)
* `bulk_indexing_clients` (default: 8)
* `ingest_percentage` (default: 100)
* `number_of_shards` (default: 1)
* `number_of_replicas` (default: 0)
* `search_clients` (default: 1)

### License
Terms and Conditions for using the MS MARCO datasets can be found at https://microsoft.github.io/msmarco/

### Citation
@article{bajaj2016ms,
title={Ms marco: A human generated machine reading comprehension dataset},
author={Bajaj, Payal and Campos, Daniel and Craswell, Nick and Deng, Li and Gao, Jianfeng and Liu, Xiaodong and Majumder, Rangan and McNamara, Andrew and Mitra, Bhaskar and Nguyen, Tri and others},
journal={arXiv preprint arXiv:1611.09268},
year={2016}
}
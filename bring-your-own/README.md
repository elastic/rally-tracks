# ESRally Track: Search Template Benchmark

This track is used for Elasticsearch search benchmarking based on your own data and your own search template. It is commonly used to test different index options such as index size, sharding, mappings, and settings. It can also be used to test different search templates, such as loose or tight fuzziness, and to compare search performance across Elasticsearch versions.

The Kibana sample data can be used as an example of how to construct the required files, but the track itself is designed for your own benchmark setup.

This track can also be used offline when you already have a fixed dataset, a search template, and the query inputs available locally as it does not require any external data sources or live sample data.

## File structure

```
.rally/benchmarks/tracks/default/bring-your-own/
├── track.json            # Track definition
├── track.py              # ParamSource: RandomParamSource
├── queries.csv           # CSV file with one query per line
├── params.json           # Optional JSON params file with template defaults
├── README.md             # This file
└── _tests/               # Validation tests
```

- `track.json`: Defines the track, operations, and challenges.
- `track.py`: Custom Python param source to supply randomized query strings.
- `queries.csv`: Input dataset for random queries. Each row should contain a realistic query string.
- `params.json`: Query parameters used in the search template.

## Requirements

- Elasticsearch Rally is installed on a load driver.
- The load driver has access to the target Elasticsearch cluster.
- An index or alias to be queried already exists in the target Elasticsearch cluster.
- The search template already exists in the target Elasticsearch cluster (for example via `PUT _scripts/<name>`).
- A `queries.csv` file (provided via `queries_file`) contains random query strings.
- An optional `params.json` file (provided via `params_file`) contains any additional params used by the search template.

## Common Rally options

- `--track-path`: Path to the track folder
- `--pipeline=benchmark-only`: Runs only the benchmark operations and skips system setup
- `--target-hosts`: Elasticsearch hosts containing the target index and search template
- `--client-options`: Connection settings such as `api_key` or both `basic_auth_user` and `basic_auth_password`; set `use_ssl` as required
- `--telemetry`: Collect node-level telemetry, defined in `.rally/rally.ini`
- `--kill-running-processes`: Stop any previous Rally processes
- `--user-tags`: Add custom tags to the run
- `--track-params`: Supply runtime parameters such as `index`, `search_template`, `queries_file`, and optionally `params_file`
- `--challenge`: Select the challenge schedule, such as `dryrun` or `real`

## Benchmarking with your own data

Use this track when you already have:

- an index with searchable documents
- a search template deployed in Elasticsearch
- a CSV file of query terms for `queries_file`
- optionally a JSON file for `params_file` when your template needs more than `query_string`

### Example command

> Important: when using an inline `--track-params` string, the final key/value pair should not end with a `.json` file path. Rally will try to open the whole argument as a file if it detects a trailing `.json`, so the order of entries matters.

```bash
esrally race \
  --track-path=bring-your-own \
  --pipeline=benchmark-only \
  --target-hosts=<es_cluster_endpoint>:443 \
  --client-options="basic_auth_user:my_user,basic_auth_password:my_password,use_ssl:True" \
  --telemetry="node-stats" \
  --kill-running-processes \
  --user-tags="model:my_tag" \
  --track-params="index:my_index,search_template:my_search_template,params_file:/tmp/my_params.json,queries_file:/tmp/my_queries.csv" \
  --challenge="dryrun"
```

If Rally raises a `FileNotFoundError`, move the `params_file` entry before the trailing value or use a dedicated JSON file for `--track-params`.

This file is optional and is useful when your template needs more than just `query_string`.

---

## Kibana sample data as an example

The Kibana sample data is useful as an example of how to structure the inputs for this track, but it is not a separate benchmark mode. It can help you understand the expected file layout and parameter shapes when building your own benchmark.

### Example template

This example uses the Kibana sample index [kibana_sample_data_flight](https://www.elastic.co/docs/manage-data/ingest/sample-data):

```json
PUT _scripts/kibana_sample_flight_search_template
{
  "script": {
    "lang": "mustache",
    "source": {
      "query": {
        "match": {
          "DestCityName": "{{query_string}}"
        }
      },
      "from": "{{from}}{{^from}}0{{/from}}",
      "size": "{{size}}{{^size}}10{{/size}}"
    }
  }
}
```

### Example `params_file`, see `./params.json`

```json
{
  "from": 0,
  "size": 5
}
```

### Example `queries_file`, see `./queries.csv`

```text
Paris
New York
Tokyo
Sydney
```

### Example request

```json
POST kibana_sample_data_flights/_search/template
{
  "id": "kibana_sample_flight_search_template",
  "params": {
    "query_string": "Paris",
    "from": 0,
    "size": 5
  }
}
```
### Example command when using kibana sample flight files

Important: when `params_file` and `queries_file` are not specified in `--track-params`, the default files in this folder will be used instead.

```bash
esrally race \
  --track=bring-your-own \
  --pipeline=benchmark-only \
  --target-hosts=<es_cluster_endpoint>:443 \
  --client-options="basic_auth_user:my_user,basic_auth_password:my_password,use_ssl:True" \
  --telemetry="node-stats" \
  --kill-running-processes \
  --user-tags="model:my_tag" \
  --track-params="index:kibana_sample_data_flights,search_template:kibana_sample_flight_search_template" \
  --challenge="dryrun"
```
---

## Notes

- Use your own index, search template, and query set for the real benchmark.
- Adjust the `clients`, `warmup-iterations`, `iterations` in the `real` challenges as required.
- Keep `queries_file` aligned with the actual query terms your template expects.
- If you use custom template parameters, prefer `params_file` so defaults stay out of the Python code.
- The sample file [bring-your-own/params.json](params.json) is just an example and can be replaced with your own values.

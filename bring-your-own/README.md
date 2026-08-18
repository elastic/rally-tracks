# ESRally Track: Search Template Benchmark

This track allows benchmarking Elasticsearch search templates with randomized query inputs from a CSV file.
It uses raw-request with a custom param-source to select random query strings and supports an optional JSON params file for custom template parameters.

## File Structure

```
.rally/benchmarks/tracks/search_template/
├── track.json            # Track definition
├── track.py              # ParamSource: RandomParamSource
├── queries.csv           # CSV file with one query per line
├── params.json           # Optional JSON params file with default template params
└── README.md             # This file
```
 - track.json: Defines the track, operations, and challenges.
 - track.py: Custom Python param source to supply randomized query strings.
 - queries.csv: Input dataset for random queries. Each row should contain a realistic query string, which can include multiple terms. Providing realistic queries helps simulate actual search workloads and produces more accurate benchmarking results.
 - params.json: Optional template parameter defaults for your search template, such as `from` and `size`, when you want to keep those values out of the Python code.


## Requirements
-	Elasticsearch Rally￼installed on a load driver. This machine needs to have sufficient CPU to generate the load for large number of clients. 
-	The load driver needs to have access to the target Elasticsearch cluster and the monitoring cluster.
-	The search template must exist in your cluster (defined with `PUT _scripts/<name>`)


## Explanation of Options
-	`--track-path`: Path to the track folder
-	`--pipeline=benchmark-only`: Only runs the track operations, no system setup
- `--target-hosts`: Elasticsearch hosts contains the target index and search template
-	`--client-options`: Connection options, authenticate with either `api_key` or `basic_auth_user` with `basic_auth_password`. Set `use_ssl` as required.
-	`--telemetry`: Collect node-level telemetry, defined in `.rally/rally.ini`
-	`--kill-running-processes`: Stop any previous Rally processes
-	`--user-tags`: Add custom tags to the run
-	`--track-params`: Specify runtime parameters (`index`, `search_template` and `queries_file`)
-	`--challenge`: Specify challenge schedule (e.g., `dryrun` (for one client and one iteration) or `real`)

## Running the Track

Bring your own `index`, `search_template` and `queries_file` example Command:
```
esrally race \
  --track-path=<path_to>/.rally/benchmarks/tracks/bring-your-own \
  --pipeline=benchmark-only \
  --target-hosts=<es_cluster_endpoint>:443 \
  --client-options="api_key:'a0V...2dw==',use_ssl:True" \
  --telemetry="node-stats" \
  --kill-running-processes \
  --user-tags="model:changeme" \
  --track-params="index:my_index,search_template:my_search_template,queries_file:/tmp/my_queries.csv" \
  --challenge="dryrun"
```

Running with the built-in `kibana_sample_flight` data command:
```
esrally race \
  --track-path=<path_to>/.rally/benchmarks/tracks/bring-your-own \
  --pipeline=benchmark-only \
  --target-hosts=<es_cluster_endpoint>:443 \
  --client-options="api_key:'a0V...2dw==',use_ssl:True" \
  --telemetry="node-stats" \
  --kill-running-processes \
  --user-tags="model:changeme" \
  --track-params="index:kibana_sample_data_flight,search_template:kibana_sample_flight_search_template,queries_file:/tmp/kibana_sample_flight_queries.csv,params_file:/tmp/kibana_sample_flight_params.json" \
  --challenge="dryrun"
```

- `search_template`:
The following `kibana_sample_flight_search_template` will work with the [kibana_sample_data_flight](https://www.elastic.co/docs/manage-data/ingest/sample-data) index:
```
PUT _scripts/kibana_sample_flight_search_template
{
  "script": {
    "lang": "mustache",
    "source": {
      "query": {
        "match": {
          "DestCityName": "{{query_string}}"
        },
        "from": "{{from}}{{^from}}0{{/from}}",
        "size": "{{size}}{{^size}}10{{/size}}"
      }
    }
  }
}
```

- Example `params_file`:
Once the sample index `kibana_sample_data_flight` is ingested, and the `kibana_sample_flight_search_template` search template is implemented, you can test the execution with the following:
```
POST kibana_sample_data_flights/_search/template
{
  "id": "kibana_sample_flight_search_template",
  "params": {
    "query_string": "Paris"
  }
}
```

This is also the shape used in `params.json` for the track. Example:
```json
{
  "query_string": "Paris"
}
```

- Example `queries_file`:
```
Paris
New York
Tokyo
Sydney
```

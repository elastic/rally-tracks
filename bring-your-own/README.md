# ESRally Track: Search Template Benchmark

This track allows benchmarking Elasticsearch search templates with randomized query inputs from a CSV file.
It uses raw-request with a custom param-source to select random query strings.

## File Structure

```
.rally/benchmarks/tracks/search_template/
├── track.json            # Track definition
├── track.py              # ParamSource: RandomParamSource
├── queries.csv           # CSV file with one query per line
└── README.md             # This file
```
 - track.json: Defines the track, operations, and challenges.
 - track.py: Custom Python param source to supply randomized query strings.
 - queries.csv: Input dataset for random queries. Each row should contain a realistic query string, which can include multiple terms. Providing realistic queries helps simulate actual search workloads and produces more accurate benchmarking results.


## Requirements
-	Elasticsearch Rally￼installed on a load driver. This machine needs to have sufficient CPU to generate the load for large number of clients. 
-	The load driver needs to have access to the target Elasticsearch cluster and the monitoring cluster.
-	The search template must exist in your cluster (defined with `PUT _scripts/<name>`)


## Explanation of Options
-	`--track-path`: Path to the track folder
-	`--pipeline=benchmark-only`: Only runs the track operations, no system setup
- `--target-hosts`: Elasticsearch hosts contains the target index and search template
-	`--client-options`: Connection options, including api_key and use_ssl
-	`--telemetry`: Collect node-level telemetry, defined in `.rally/rally.ini`
-	`--kill-running-processes`: Stop any previous Rally processes
-	`--user-tags`: Add custom tags to the run
-	`--track-params`: Override runtime parameters (`index` and `search_template`)
-	`--challenge`: Specify challenge schedule (e.g., `dryrun` or `real`)

## Running the Track

Example Command:
```
esrally race \
  --track-path=<path_to>/.rally/benchmarks/tracks/search_template \
  --pipeline=benchmark-only \
  --target-hosts=<preprod_es_cluster_endpoint>:443 \
  --client-options="api_key:'a0V...2dw==',use_ssl:True" \
  --telemetry="node-stats" \
  --kill-running-processes \
  --user-tags="model:changeme" \
  --track-params="index:my_index,search_template:my_search_template" \
  --challenge="dryrun"
```

## Example queries.csv
```
common wealth bank
apple banana orange
```

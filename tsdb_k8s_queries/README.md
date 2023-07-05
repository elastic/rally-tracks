## TSDB k8s query track

The main goal of the TSDB k8s query track is to measure the performance of common k8s integration search requests.
The queries, index templates and corpus data try to match production as close as possible.

### The search requests

The search requests of the following visualizations have been included in this track:
* Average CPU usage per pod.
* Average memory usage per pod.
* Average cpu per container.
* Average memory per container.
* Average node cpu usage per container.
* Average node memory usage per container.
* Unique deployment count.
* Percentile cpu usage per container.
* Status per pod.
* Transmitted network usage per pod.

The search request is sourced from Kibana Lens in the k8s integration. For each of this search request a template is defined in operations.
From each template, three search requests are generated. First with the last 15 minutes filter, then the last 2 hours filter, and finally with a last 24-hour interval. In case a `date_histogram` is used in the query template then each of these variations uses a different interval. A fixed interval of 30 seconds, 1 minute, and 30 minutes respectively.

The k8s visualizations that run these queries don't run very often or under a high query load.
Often these visualizations are loaded and then sometime later re-loaded. This triggers the shards of the k8s pod and container data streams to go search-idle. However, indexing always happens in the background. When shards become search-active again, a refresh needs to occur as part of the search request. This track is designed to emulate this runtime behaviour.

The way that this is emulated is by executing search and bulk operations concurrently. For each of the mentioned visualization there is a search operation and a corresponding bulk operation with a `touch-*` prefix as name. Both of the search and bulk operation are run concurrently using a `parallel` task. The bulk operations perform minimal indexing (1 index client and one document per bulk request) and reindexes the same corpus with a different `@timestamp` field using an ingest processor. This is sufficient so that the refresh isn't a noop. Also the data streams are configured with a `index.search.idle.after` of `1s`, so that shards of the backing indices become search-idle after 1 second of the last search request. Additionally, the search operations are configured to only execute a search every 4 seconds.

When the data sets are updated, the `end_time` constant and `time_intervals` dictionary in the `track.json` file must be updated.
The `end_time` should match with the `@timestamp` field of latest document in the data files. Note that this timestamp should be the same for both pod and container k8s data sets.
The `time_intervals` dictonary control for each search request template fixed interval used in date_histogram and the range query on the `@timestamp` field.
The timestamp the dictonary value entry need to be updated based on what the `end_time` has been set. For example the value for `15_minutes` key the timestamp shoud be `end_time` - 15 minutes. Note that Kibana doesn't use dath math and therefor these queries don't use that too. This to emulate production as close as possible.

### Generation of data

New Corpora data can be generated with the help of [Elastic-integration-corpus-generator-tool How_to_Guide](https://github.com/elastic/observability-dev/blob/main/docs/infraobs/cloudnative-monitoring/dev-docs/elastic-generator-tool-with-rally.md).

Specific templates are implemented as part of the generator tool. Based on them, sample datasets needed for the rally track have already been generated and uploaded to public GCP bucket for reuse.

### Generation of Templates

Along with generation of data, a rally track might also need updated template files for the specific datasets that will index.

Follow below process to extract the latest index templates for specific package version:

1. Create local Elastic stack

```bash
elastic-package stack up -d -vvv --version=8.7.1
```

1. Login to Kibana (https://localhost:5601) and install specific integration. `Eg. Kubernetes Integration v1.39.1`
   The installation of package will install index templates in local Elasticsearch.

2. Export needed environmental variables

```bash
 elastic-package stack shellinit
 export ELASTIC_PACKAGE_ELASTICSEARCH_HOST=https://127.0.0.1:9200
 export ELASTIC_PACKAGE_ELASTICSEARCH_USERNAME=elastic
 export ELASTIC_PACKAGE_ELASTICSEARCH_PASSWORD=changeme
 export ELASTIC_PACKAGE_KIBANA_HOST=https://127.0.0.1:5601
 export ELASTIC_PACKAGE_CA_CERT=~/.elastic-package/profiles/default/certs/ca-cert.pem
 ```

 4. Use elastic-package dump command:

```bash
 elastic-package dump installed-objects --package kubernetes

 [output] ...
 packages exttracted to package-dump
 ```

5. Locate and use your needed index templates

```bash
 cd package-dump/index_templates
  - metrics-kubernetes.pod.json
  - metrics-kubernetes.container.json 
```

### Parameters

This track allows to overwrite the following parameters using `--track-params`:

* `bulk_size` (default: 9000)
* `touch_bulk_size` (default: 50): The bulk size for bulk requests executed during searching.
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `touch_bulk_indexing_clients` (default: 3): Number of clients that issue bulk indexing for the bulk tasks that get executed during searching.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `force_merge_max_num_segments` (default: unset): An integer specifying the max amount of segments the force-merge operation should use.
* `number_of_replicas` (default: 0)
* `number_of_shards` (default: 1)

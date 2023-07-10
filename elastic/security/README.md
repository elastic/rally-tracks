# Elastic Security Track

This track simulates security workloads.

The track supports the following functionality:

- **Bulk Indexing** - Bulk Indexing of a representative data set. Each dataset is generated prior to indexing from source corpora, that originate from sample data for Elastic integrations that are commonly used for the use case.
- **Simulated Queries** - Queries that are representative of the use case. These queries represent common queries issued by Kibana for the target use case. Query execution aims to imitate Kibana query execution as close as possible, with respect to concurrency and hierarchical execution.

## Pre-requisites

Depending on the parameters provided, the data set can become very large, in the order of several hundred GB. By default, the data are stored in [Rally's benchmark data directory](https://esrally.readthedocs.io/en/stable/configuration.html#benchmarks). Ensure that you have enough free disk space to store the data in this directory.


## Key Concepts & Methodology

### Indexing

Indexing consists of 3 key stages performed in sequence:

#### 1. Data Download

Corpora datasets are downloaded. Each corpus represents an [Elasticsearch integration](https://www.elastic.co/integrations).  The selected corpus are configured by the parameter [integration_ratios](#ratios).

The default integrations downloaded are `auditbeat, filebeat, metricbeat, packetbeat, winlogbeat`.

Security endpoint events with types `file, library, network, process, registry and security` are included in the `logs-endpoint` integration represent a dataset extracted from the security endpoint.

#### 2. Data Generation

Prior to any indexing, a data generation stage is performed. This considers all of the corpora available, and generates a dataset according to configured ratios. These [ratios](#ratios) are configurable, although it is anticipated that defaults should be appropriate in all but exceptional circumstances.

The only currently supported generation mode is `Raw`. This simulates traffic as sent by the Elastic agent and assumes Elasticsearch ingestion pipelines will be used to enrich data according to the source. This is currently the only supported mode.

**Important Note**: When specifying corpus ratios, we use the document size for the security use case which differs from the logging use case.

The volume of data to index is controlled through the parameter `raw_data_volume_per_day` and the time span between via `start_date` and `end_date` - see [Data Indexing](#3-data-indexing). As described above, `raw_data_volume_per_day` represents the volume of original data to index and not the total JSON e.g. for logging this represents the volume of raw log files on disk to simulate.
		
Whilst the volume of data generated is inferred by the volume per day and time range specified, a limit can also be placed on the [maximum data](#data-generation-parameters) generated in this stage. This specifies an upper limit on the volume of disk space to use for file generation - corpus ratios will still be respected within this limit. Additionally, the [number of threads](#data-generation-parameters) used for data generation is configurable and can be used to improve speed of generation assuming sufficient I/O is available.
		
Note: By default, downloaded and generated data is re-used on subsequent runs if the data exists on disk and track parameters which influence data generation have not changed. This saves unnecessary computation which can be expensive for tests involving larger data volumes. The current parameters which impact data generation are:

- raw_data_volume_per_day
- max_generated_corpus_size
- data_generation_clients
- max_total_download_gb
- start_date
- end_date
- integration_ratios

Should any of the above be changed between runs, data will be re-generated.

#### 3. Data Indexing

The dataset is indexed with each event being sent to the appropriate [data stream](https://www.elastic.co/guide/en/elasticsearch/reference/master/data-streams.html), for the corpus and integration from which it originated. All indexing utilises Data Streams and Composable Templates, with mappings and ingestion pipelines aligned with the appropriate Elastic integration.

The [number of indexing threads](#indexing-parameters) can be configured as can the [number of primary and replica shards](#indexing-parameters). If changing the number of primary or replica shards, be aware this will change the setting for all data streams.

### 4.  Querying

Querying is exposed through the concept of workflows. A workflow represents a linear series of user actions in Kibana e.g. a "Network Dashboard" workflow might consist of the following 4 actions:

1. Opening the Network dashboard with a timespan from `now-24hr` to `now`.
2. Selecting a sub-tab on the page
3. Applying a timespan restriction
4. Filtering on ip address

Each of these user actions potentially involve many Elasticsearch queries, often issued in parallel and hierarchically. A user action is represented using a [composite](https://esrally.readthedocs.io/en/latest/track.html#composite) rally query, consisting of many parallel branches of query execution. Each composite query is stored in a numerically delimited file, under a folder representing the workflow. For example, consider this [Network Dashboard](https://github.com/elastic/rally-tracks/tree/master/elastic/security/workflows/network) workflow.

The track aims to simulate a Kibana load. This is modelled as a set of workflows all executing concurrently at random intervals. Each workflow executes their actions sequentially until completion. An exponentially distributed random delay occurs between each action -  the mean of this distribution can be controlled through the parameter `think_time_interval`. This simulates the user pausing and thinking between actions. A random delay (also exponentially distributed and controlled via a parameter `workflow_time_interval`) occurs between executing workflows. This is the main parameter users should use to control individual levels of user activity.

The queries contained within this track represent realistic Elasticsearch queries resulting from Kibana usage. Given Kibana's popularity for time series data, these queries often contain date operations and restrictions e.g. date range queries. In order to ensure queries match, these date ranges must be modified at run time time prior to being executed against Elasticsearch.

#### Modifying Query Behavior

By and large, this track can query in two modes: a "real time" mode, wherein the indexing and querying are happening concurrently and the query window continues to shift forward over the duration of execution, and a "static" mode, wherein the data has already been indexed (or perhaps is being indexed, less commonly), but the query executes from a fixed time frame.

To accomplish different behaviors in the query phase(s) of a given challenge, we introduce the track-level parameters `query_min_date`, `query_max_date`, `query_max_date_start`, and `query_average_interval`.  Examples are given at [modifying query behavior](https://github.com/elastic/rally-tracks/tree/master/elastic/logs#modifying-query-behavior).

## Track Parameters

The following parameters are available:

* `wait_for_status` (default: `green`) - The track creates Data Streams prior to indexing. All created Data Streams must at least reach this status before indexing commences. Reduce to `yellow` for clusters where green isn't possible e.g. single node.
* `corpora_uri_base` (default: `https://rally-tracks.elastic.co`) - Specify the base location of the datasets used by this track.

### Data Generation Parameters

* `data_generation_clients` (default: `2`) - The number of concurrent clients used for data generation. Increase to speed up data generation assuming sufficient IO.
* `max_generated_corpus_size` (default: `2GB`) - Sets an upper limit for the size of the generated corpus, allowing the user to limit disk space usage. Accepts units `M`, `MB`, `G`, `GB`, `T`, `TB`, `P`, `PB`.
* `force_data_generation` (default: `false`) - If set to `true`, file generation always takes place. If `false` and generated files exist in `{file_cache_dir}/{unique_id}` they are re-used and generation is skipped. The `unique_id` here will be a hash of the parameters which effect data generation - see [Data Generation](#2-data-generation).
* `random_seed` (default: 13) - Files are generated through random sampling of the source corpora. This pseudo random selection process is seeded to ensure multiple runs of the track generate the same data - thus ensuring tests are repeatable. Changing this value or `data_generation_clients` will cause the generation of a different dataset. Must be an integer.
* `integration_ratios` - A dictionary containing a key per integration. Each integration in turn has a configuration object. This object includes a `corpora` dictionary, containing the ratios of the source corpora to use for this integration in the generated corpus. The keys represent the corpus names and the values the ratios - ratios across all integrations must add up to 1. See [Ratios](#ratios) for further details.


### Indexing Parameters

* `number_of_shards` (default: 1) - The number of primary shards to set per Data Stream. The same value is used for all Data Streams.
* `number_of_replicas` (default: 1) - The number of replicas to set per Data Stream. The same value is used for all Data Streams.
* `bulk_indexing_clients` (default: 8) - The number of clients issuing indexing requests.
* `bulk_size` (default: 50) - The number of documents to send per indexing request.

### Querying parameters

* `workflow_time_interval` (default: 30) - The mean time between executions of a workflow. A Poisson process resulting in an exponentially distributed delay.
* `think_time_interval` (default: 4) - The mean time between the execution of actions of a workflow. A Poisson process resulting in an exponentially distributed delay. Users of the track shouldn't need to modify this parameter.
* `query_warmup_time_period` (default: 120) - Warmup time for queries before measurements are recorded.
* `query_time_period` (default: 900) - The period for which queries should be issued. This only applies to challenges where no concurrent indexing is occurring. If concurrent indexing is occurring, querying will stop once this completes.
* `random_seed` (default: 13) - Integer used to determine the order of query execution. The interval between workflow executions, as well as the actions within them, is based on an exponentially distributed random variable. Seeding this process ensures execution is deterministic across different executions.
* `query_min_date` (default: `2020-01-01`) - Minimum datetime to execute queries over (such as yyyy-MM-dd or yyyy-MM-ddThh:mm:ss.zzzZ). Affects ranges and date_histograms.  Must be less than `query_max_date` (or `query_max_date_start`).
* `query_max_date` (default: `2020-01-02`) - Maximum datetime to execute queries over (such as yyyy-MM-dd or yyyy-MM-ddThh:mm:ss.zzzZ). Affects ranges and date_histograms. Cannot be configured when `query_max_date_start` is also defined. 
* `query_max_date_start` (optional) - Maximum datetime to execute queries over, at the beginning of a query workflow task. Increments with the time elapsed as the benchmark executes. Cannot be configured when `query_max_date` is also defined.
* `query_average_interval` (optional) - Average time interval for queries to use. If unset, we use the durations and intervals set in the original action definitions.
* `query_request_params` (optional) - A map of query parameters that will be used with any querying.
* `query_workflows` (optional) - A list of workflows to execute. By default, all workflows are used.

## Available Challenges

The following challenges are currently subject to change.

### Security Indexing (security-indexing)

This challenge aims to establish the indexing throughput that can be supported by an Elasticsearch cluster. This challenge indexes the specified volume. No queries are issued. Index throttling can be enabled via the parameter `bulk_indexing_clients`.

In order to optimise indexing throughput, users may wish to consider modifying the `bulk_indexing_clients` and `bulk_size`.

### Security Querying (security-querying)

This challenge simulates Kibana load via so-called workflows. Workflows execute concurrently at random intervals, and each workflow executes their actions sequentially until completion. An exponentially distributed random delay occurs between each action - the mean of this distribution can be controlled through the parameter `think_time_interval`. This simulates the user pausing and thinking between actions. A random delay (also exponentially distributed and controlled via a parameter `workflow_time_interval`) occurs between executing workflows. This is the main parameter users should use to control individual levels of user activity. Queries will be issued for the period specified by the parameter `query_time_period`. No indexing will occur.

Users of this track may use this challenge to execute queries on an existing index for which bulk indexing has completed e.g. after using the challenge `#Security Indexing`.

### Security Indexing and Querying (security-indexing-querying)

This challenge executes indexing and querying sequentially. Queries will be issued concurrently until `query_time_period` has elapsed.

### Generate source events for detection rules (generate-alerts-source-events)

This challenge is a demo usage of [Geneve](https://github.com/elastic/geneve) via the `events-emitter-source` [parameter source](https://github.com/elastic/rally-tracks/blob/master/elastic/security/parameter_sources/events_emitter.py), it generates source events but does not interact with anything else. It's executed as part of the [it/test_security.py](https://github.com/elastic/rally-tracks/blob/master/it/test_security.py) integration tests. Currently, Geneve is pinned to version [v0.2.0](https://github.com/elastic/rally-tracks/blob/master/elastic/security/track.json#L410). This is the only challenge that depends on Geneve and pyyaml (Geneve requires pyyaml).

## Ratios

By default, the track generates a dataset by sampling the source corpora randomly according to defined ratios. These ratios can be changed through the parameter `integration_ratios`. 

This parameter must be passed as a dictionary where the top level keys represent the integration names. Each integration in turn has its own dictionary with a `corpora` object.  This object describes the corpora associated with the integration as well as the ratios to use when generating the dataset. The ratios values are recalculated to a percentage of the total data generated. Changing this value requires the user to understand which corpora are associated with which integrations - this thus represents an advanced use case.

As an example, the following includes integrations for `auditbeat`, `filebeat`, `metricbeat`, `winlogbeat` and `logs-endpoint`:
```
{
  "auditbeat": {
     "corpora": {
        "auditbeat-security": 1.0
     }
  },
  "filebeat": {
     "corpora": {
        "filebeat-security": 1.0
     }
  },
  "metricbeat": {
     "corpora": {
        "metricbeat-security": 1.0
     }
  },
  "winlogbeat": {
     "corpora": {
        "winlogbeat-security": 1.0
     }
  },
  "logs-endpoint": {
     "corpora": {
        "endpoint-events-file": 0.2,
        "endpoint-events-library": 0.1,
        "endpoint-events-network": 0.2,
        "endpoint-events-process": 0.3,
        "endpoint-events-registry": 0.1,
        "endpoint-events-security": 0.1
     }
  }
}
```

The parameter `integration_ratios` is best set via a track parameter file as described here [here](https://esrally.readthedocs.io/en/stable/command_line_reference.html#track-params). 


## Integrations

Benchmarking in real world conditions requires keeping in sync with index mappings, templates, pipelines, etc. Currently this is a manual effort involving the [integration packages](https://github.com/elastic/integrations) as external dependency.

These are the integrations in use:

- endpoint (package at [endpoint-package](https://github.com/elastic/endpoint-package))

### Upgrading the integrations

You need to load the integrations into a running Kibana instance and then copy their assets to the track. The following instructions use `elastic-package`, which requires that each integration is packaged, with the wanted version already published to the [Elastic Package Registry](https://epr.elastic.co/search).

#### Steps for loading the integration

- Install elastic-package, see the [README](https://github.com/elastic/elastic-package/#readme)
- Download the integration source, ie: `wget https://github.com/elastic/endpoint-package/archive/refs/tags/v8.2.0.tar.gz`
- Start the stack, ie: `elastic-package stack up --version 8.2.0`
- Load the integration, ie: `cd endpoint-package-8.2.0/package/endpoint && elastic-package install endpoint`

#### Steps for updating the assets

- Dump the integration's assets, ie: `elastic-package dump installed-objects -p endpoint -o endpoint-assets`
- Copy the relevant files, ie:
  ```
  cp endpoint-assets/component_templates/logs-* rally-tracks/elastic/security/templates/component
  cp endpoint-assets/component_templates/.fleet_* rally-tracks/elastic/security/templates/component
  cp endpoint-assets/index_templates/logs-* rally-tracks/elastic/security/templates/composable
  cp endpoint-assets/index_templates/.logs-* rally-tracks/elastic/security/templates/composable
  cp endpoing-assets/ingest_pipelines/logs-* rally-tracks/elastic/security/pipelines
  cp endpoint-assets/ingest_pipelines/.fleet_final_pipeline-*.json rally-tracks/elastic/security/pipelines
  ```
- **Some of the assets are versioned, cautiously add the new files and remove the old. Some files might just be new in the package, consider adding them also in the track.**

## Elasticsearch Compatibility

Currently only Elasticsearch 7.17+ is supported due to the installed integration versions.

## Versioning Scheme

https://esrally.readthedocs.io/en/stable/track.html#track-repositories-branch-logic

## How to Contribute

If you want to contribute to this track, please ensure that it works against the main version of Elasticsearch (i.e. submit PRs against the master branch). We can then check whether it's feasible to backport the track to earlier Elasticsearch versions.

See all details in the [contributor guidelines](https://github.com/elastic/rally/blob/master/CONTRIBUTING.md).

## License

This software is licensed under the Apache License, version 2 ("ALv2"), quoted below.

Copyright 2015-2020 Elasticsearch [https://www.elastic.co](https://www.elastic.co)

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.




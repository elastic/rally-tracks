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

Corpora datasets are downloaded. Each corpus represents an [Elasticsearch integration](https://www.elastic.co/integrations).  The selected corpus are configured by the parameter `integrations` and include: 
```
auditbeat 
filebeat
metricbeat
packetbeat
winlogbeat
logs-endpoint
```
The default integrations downloaded are `auditbeat, filebeat, metricbeat, packetbeat, winlogbeat`.

Security endpoint events with types `file, library, network, process, registry and security` are included in the `logs-endpoint` integration represent a dataset extracted from the security endpoint.  These can be included using the run-time parameter:
`--integrations=["logs-endpoint"]`

#### 2. Data Generation

Currently documents are read directly from the downloaded corpora datasets, skipping the data generation step.  This means the dataset used is the full downloaded corpus without adjustment.  In the future, the ratios of data from each corpus being included in the dataset will be configurable during the data generation step.
	
Note: By default, downloaded and generated data is re-used on subsequent runs if the data exists on disk and track parameters which influence data generation have not changed. This saves unnecessary computation which can be expensive for tests involving larger data volumes.

#### 3. Data Indexing

The dataset is indexed with each event being sent to the appropriate [data stream](https://www.elastic.co/guide/en/elasticsearch/reference/master/data-streams.html), for the corpus and integration from which it originated. All indexing utilises Data Streams and Composable Templates, with mappings and ingestion pipelines aligned with the appropriate Elastic integration.

The [number of indexing threads](#indexing-parameters) can be configured as can the [number of primary and replica shards](#indexing-parameters). If changing the number of primary or replica shards, be aware this will change the setting for all data streams.

### Querying

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

This challenge issues queries at the rate determined by the parameters `number_of_users`,  `workflow_time_interval` and `think_time_interval`. Queries will be issued for the period specified by the parameter `query_time_period`. No indexing will occur.

Users of this track may use this challenge to execute queries on an existing index for which bulk indexing has completed e.g. after using the challenge `#Security Indexing`.

### Security Indexing and Querying (security-indexing-querying)

This challenge executes indexing and querying sequentially. Queries will be issued concurrently until `query_time_period` has elapsed.


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




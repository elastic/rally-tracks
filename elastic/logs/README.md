# Elastic Logs Track

This track simulates logging workloads.

The track supports the following functionality:

- **Bulk Indexing** - Bulk Indexing of a representative data set. Each dataset is generated prior to indexing from source corpora, that originate from sample data for Elastic integrations that are commonly used for the use case.
- **Date Profiles** - Events do not arrive uniformly in any realistic use case, with spikes of indexing occurring during certain days and hours. We refer to this as the "date profile" of the data. This track allows this date profile to be customised.
- **Throttled Indexing** - Indexing can be both throttled to ensure a date profile is respected i.e. events arrive to the Elasticsearch index at the appropriate rate as defined by the date profile.
- **Simulated Queries** - Queries that are representative of the use case. These queries represent common queries issued by Kibana for the target use case. Query execution aims to imitate Kibana query execution as close as possible, with respect to concurrency and hierarchical execution.

## Pre-requisites

Depending on the parameters provided, the data set can become very large, in the order of several hundred GB. By default, the data are stored in [Rally's benchmark data directory](https://esrally.readthedocs.io/en/stable/configuration.html#benchmarks). Ensure that you have enough free disk space to store the data in this directory.

## Key Concepts & Methodology

### Indexing

Indexing consists of 3 key stages performed in sequence:

#### 1. Data Download

Corpora datasets are downloaded. Each corpus represents an [Elasticsearch integration](https://www.elastic.co/integrations). The total volume of data download and available for use in the subsequent data generation stage is configurable through the parameter `max_total_download_gb` - see [Data Download](#data-download-parameters).

#### 2. Data Generation

Prior to any indexing, a data generation stage is performed. This considers all of the corpora available, and generates a dataset according to configured ratios. These [ratios](#ratios) are configurable, although it is anticipated that defaults should be appropriate in all but exceptional circumstances.

The only currently supported generation mode is `Raw`. This simulates traffic as sent by the Elastic agent and assumes Elasticsearch ingestion pipelines will be used to enrich data according to the source. This is currently the only supported mode.

**Important Note**: When specifying corpus ratios, these refer to the ratios of original raw data. For the logging use case, we use the `message` field to estimate the number of bytes of the original raw log line. When a log message is converted to JSON it inherently increases in size due to the associated notation overhead. The Elastic agent adds further meta fields e.g. `host_name`, which cause this size to increase further. This "raw to JSON expansion factor" N, means that 1GB of raw data will actually equate to NGB of JSON on disk. The actual ratios of the final JSON for each corpus may also be different: as different corpus have different JSON fields, and thus raw to JSON expansion factors, causing the ratios of the final JSON to diverge from the original corpus ratios. For common questions regards this see the [FAQ](#faq).

The volume of data to index is controlled through the parameter `raw_data_volume_per_day` and the time span between via `start_date` and `end_date` - see [Data Indexing](#3-data-indexing). As described above, `raw_data_volume_per_day` represents the volume of original data to index and not the total JSON e.g. for logging this represents the volume of raw log files on disk to simulate.
	
The original corpora datasets are very verbose. We therefore also remove some fields to ensure datasets are representative for a use case. The fields removed are configurable - see [Changing the Datasets](#changing-the-datasets).
		
Whilst the volume of data generated is inferred by the volume per day and time range specified, a limit can also be placed on the [maximum data](#data-generation-parameters) generated in this stage. This specifies an upper limit on the volume of disk space to use for file generation - corpus ratios will still be respected within this limit. Additionally, the [number of threads](#data-generation-parameters) used for data generation is configurable and can be used to improve speed of generation assuming sufficient I/O is available.
		
Note: By default, downloaded and generated data is re-used on subsequent runs if the data exists on disk and track parameters which influence data generation have not changed. This saves unnecessary computation which can be expensive for tests involving larger data volumes. The current parameters which impact data generation are:

- raw_data_volume_per_day
- max_generated_corpus_size
- data_generation_clients
- max_total_download_gb
- start_date
- end_date
- integration_ratios
- exclude_properties

Should any of the above be changed between runs, data will be re-generated.

#### 3. Data Indexing

The generated dataset is indexed with each event being sent to the appropriate [data stream](https://www.elastic.co/guide/en/elasticsearch/reference/master/data-streams.html), for the corpus and integration from which it originated. All indexing utilises Data Streams and Composable Templates, with mappings and ingestion pipelines aligned with the appropriate Elastic integration.

The user is required to specify the volume of raw data to index through the parameter `raw_data_volume_per_day`. The selected value here is in turn multiplied by the time difference between `start_date` and `end_date` to determine the total volume generated and in turn indexed. The timestamps of the data will also cover the total period from the specified `start_date` to the `end_date`. The actual amount of data sent to Elasticsearch will be greater than `raw_data_volume_per_day * (end_date-start_date))` to the conversion from raw message to JSON and addition of enrichment fields. See the [FAQ](#faq) for further details.

The [number of indexing threads](#indexing-parameters) can be configured as can the [number of primary and replica shards](#indexing-parameters). If changing the number of primary or replica shards, be aware this will change the setting for all data streams.


#### Data Profiles & Throttling

By default, documents are assigned a timestamp in the range of `start_date` (default `2020-01-01`) to `end_date` (default `2020-01-02`) with a fixed interval between documents. The oldest documents, starting at `start_date`, will be indexed first and the data streams filled "forward". The default profile is effectively uniform and results in a constant N GB/sec.

All date profiles should, however, deliver the same N GB/day in total as requested by `raw_data_volume_per_day`.

In normal operation, whilst a date profile is assigned to the data, actual indexing is effectively un-throttled i.e. Rally will index as fast as possible. Throttling can be explicitly enabled with the boolean parameter `throttle_indexing`. This causes the data profile and interval between events to be respected, limiting indexing throughput to the appropriate N GB/sec.

### Querying

Querying is exposed through the concept of workflows. A workflow represents a linear series of user actions in Kibana e.g. a "Nginx Dashboard" workflow might consist of the following 4 actions:

1. Opening an Nginx dashboard with a timespan from `now-24hr` to `now`.
2. Filtering on a specific error code
3. Applying a timespan restriction
4. Filtering on geo location

Each of these user actions potentially involve many Elasticsearch queries, often issued in parallel and hierarchically. A user action is represented using a [composite](https://esrally.readthedocs.io/en/latest/track.html#composite) rally query, consisting of many parallel branches of query execution. Each composite query is stored in a numerically delimited file, under a folder representing the workflow. For example, consider this [nginx](https://github.com/elastic/rally-tracks/tree/master/elastic/logs/workflows/nginx) workflow.

The track aims to simulate a Kibana load. This is modelled as a set of workflows all executing concurrently at random intervals. Each workflow executes their actions sequentially until completion. An exponentially distributed random delay occurs between each action -  the mean of this distribution can be controlled through the parameter `think_time_interval`. This simulates the user pausing and thinking between actions. A random delay (also exponentially distributed and controlled via a parameter `workflow_time_interval`) occurs between executing workflows. This is the main parameter users should use to control individual levels of user activity.

The queries contained within this track represent realistic Elasticsearch queries resulting from Kibana usage. Given Kibana's popularity for time series data, these queries often contain date operations and restrictions e.g. date range queries. In order to ensure queries match, these date ranges must be modified at run time time prior to being executed against Elasticsearch.

#### Modifying Query Behavior

By and large, this track can query in two modes: a "real time" mode, wherein the indexing and querying are happening concurrently and the query window continues to shift forward over the duration of execution, and a "static" mode, wherein the data has already been indexed (or perhaps is being indexed, less commonly), but the query executes from a fixed time frame.

To accomplish different behaviors in the query phase(s) of a given challenge, we introduce the track-level parameters `query_min_date`, `query_max_date`, `query_max_date_start`, and `query_average_interval`.

##### Example 1 - Static Query Dates
```
{
    "start_date": "2020-01-01",
    "end_date": "2020-01-02",
    "query_min_date": "2020-01-01",
    "query_max_date": "2020-01-02"
}
``` 
The above configuration is equivalent to the defaults for these values. This type of configuration best serves the following conditions:
* The challenge separately executes the indexing and querying phases, or executes only a query phase against an already-populated Elasticsearch. This is because data is indexed sequentially into Elasticsearch, and if these tasks were executed in parallel, early queries may be hitting empty time ranges until indexing catches up to where the query ranges are defined.
* The actions within the desired workflows have ranges and intervals which reflect exactly the timeframes needed for querying. For example, a `range` query with `"@timestamp.gte": "2020-12-01T10:17:41.983Z"` and `"@timestamp.lte": "2020-12-01T12:17:41.983Z"` reflects a desired query timeframe of 2 hours. This action would retain its absolute range, and be updated dynamically to be:
```
{
...
    "range": {
      "@timestamp": {
        "gte": "2020-01-01T22:00:00.000Z",
        "lte": "2020-01-02T00:00:00.000Z",
        "format": "strict_date_optional_time"
      }
    }
...
}
```

##### Example 2 - Static Query Dates With Average Interval
```
{
    "start_date": "2020-01-01",
    "end_date": "2020-01-31",
    "query_min_date": "2020-01-01",
    "query_max_date": "2020-01-31",
    "query_average_interval": "1d"
}
```
Similarly to Example 1, Example 2 uses a static date to query "back" from, defined by the `query_max_date`. The primary difference here though is that the time ranges defined in our actions are overridden dynamically using the value of `query_average_interval`.
Our prior sample action, defined as...
```
{
...
    "range": {
      "@timestamp": {
        "gte": "2020-12-01T10:17:41.983Z",
        "lte": "2020-12-01T12:17:41.983Z",
        "format": "strict_date_optional_time"
      }
    }
...
}
```
... now will have its difference _ignored_, with the average interval used as a baseline for a variable range output. In order to simulate independent user behavior through distributed, random delays, the `query-average-interval` is used as the average for an exponential distribution, possibly yielding something like the following in a given iteration:
```
{
...
    "range": {
      "@timestamp": {
        "gte": "2020-01-27T12:00:00.000Z",
        "lte": "2020-01-31T00:00:00.000Z",
        "format": "strict_date_optional_time"
      }
    }
...
}
```

This can produce different bounds for each query defined in an action, and hence aim to be more realistic by applying a variety of load.

##### Example 3 - Dynamic Query Dates
```
{
    "start_date": "2020-01-01",
    "end_date": "2020-01-02",
    "query_max_date_start": "2020-01-01"
}
```
This configuration uses the special parameter `query_max_date_start` to indicate that the max date of the query actions should move over the course of the test. This is likely the desired configuration when the challenge executes concurrent indexing and querying, as it can be configured to better guarantee the appropriate timeframe in the early phase of the workflow to return hits from Elasticsearch as indexing is occurring live.
`query_max_date_start` indicates the max datetime _at the start of the query task_ but moves forward in real time as the task executes. For example, consider the following, defined in an action:
```
{
...
  "range": {
    "@timestamp": {
      "gte": "2020-12-01T10:17:41.983Z",
      "lte": "2020-12-01T12:17:41.983Z",
      "format": "strict_date_optional_time"
    }
  }
...
}
```
At the start of our query workflow, it would be re-evaluated (approximately) as:
```
{
...
  "range": {
    "@timestamp": {
      "gte": "2019-12-31T22:00:00.000Z",
      "lte": "2020-01-01T00:00:00.000Z",
      "format": "strict_date_optional_time"
    }
  }
...
}
```
Five minutes after the start of our query workflow, it would look like this:
```
{
...
  "range": {
    "@timestamp": {
      "gte": "2019-12-31T22:05:00.000Z",
      "lte": "2020-01-01T00:05:00.000Z",
      "format": "strict_date_optional_time"
    }
  }
...
}
```
Note that `query_max_date_start` cannot be defined in conjunction with `query_max_date`.

## Track Parameters

The following parameters are available:

* `raw_data_volume_per_day` (default: `0.1GB`) - The volume of raw data to index per day. 
* `wait_for_status` (default: `green `) - The track creates Data Streams prior to indexing. All created Data Streams must at least reach this status before indexing commences. Reduce to `yellow` for clusters where green isn't possible e.g. single node.
* `start_date` (default: `2020-01-01` ) - The start date of the data. The `end_date` minus this value will determine the time range assigned to the data and also directly impact the total volume indexed. Must be less than the `end_date`.
* `end_date` (default: `2020-01-02` ) - The end date of the data. This value minus the `start_date` will determine the time range assigned to the data and also directly impact the total volume indexed. Must be greater than the `start_date`.
* `corpora_uri_base` (default: `https://rally-tracks.elastic.co`) - Specify the base location of the datasets used by this track.
* `lifecycle` (default: unset to fall back on Serverless detection) - Specifies the lifecycle management feature to use for data streams. Use `ilm` for index lifecycle management or `dlm` for data lifecycle management. By default, `dlm` will be used for benchmarking Serverless Elasticsearch.
* `workflow-request-cache` (default: `true`) - Explicit control of request cache query parameter in searches executed in a workflow. This can be further overriden at an operation level with `request-cache` parameter.
* `synthetic_source_keep` (default: unset): If specified, configures the `index.mapping.synthetic_source_keep` index setting.
* `source_mode` (default: unset) - Specifies the source mode to be used.
* `use_synthetic_source_recovery` (default: unset): Whether synthetic recovery source will be used.
* `recovery_target` (required) - The target index or data stream for fetching shard changes via the recovery API.
* `recovery_from_seq_no` (default: `0`) - The sequence number from which to start fetching translog operations.
* `recovery_poll_timeout` (default: `1m`) - The maximum time to wait for additional translog operations before returning an empty result.
* `recovery_small_max_batch_size` (default: `4MB`) - The maximum estimated size for the batch of translog operations to return.
* `recovery_large_max_batch_size` (default: `32MB`) - The maximum estimated size for the batch of translog operations to return.
* `recovery_max_operations_count (default: `16777216`) - The maximum number of translog operations to return in a single batch.
* `patterned_text_message_field` (default: `false`) - If true use `patterned_text` for all message fields, else `match_only_text`. 

### Data Download Parameters

* `max_total_download_gb` (default: `2 * num of corpus`) - The maximum volume of data to download in GB. This is divided evenly amongst each of the corpus available. A minimum of 1GB per corpus will be downloaded irrespective of this value. This value defaults to `2 * num of corpus` i.e. by default 2GB is downloaded for each corpus. Currently there are 18 corpora, requiring 36GB of space.

### Data Generation Parameters

* `data_generation_clients` (default: `2`) - The number of concurrent clients used for data generation. Increase to speed up data generation assuming sufficient IO.
* `max_generated_corpus_size` (default: `2GB`) - Sets an upper limit for the size of the generated corpus, allowing the user to limit disk space usage. Accepts units `M`, `MB`, `G`, `GB`, `T`, `TB`, `P`, `PB`.
* `force_data_generation` (default: `false`) - If set to `true`, file generation always takes place. If `false` and generated files exist in `{file_cache_dir}/{unique_id}` they are re-used and generation is skipped. The `unique_id` here will be a hash of the parameters which effect data generation - see [Data Generation](#2-data-generation).
* `random_seed` (default: 13) - Files are generated through random sampling of the source corpora. This pseudo random selection process is seeded to ensure multiple runs of the track generate the same data - thus ensuring tests are repeatable. Changing this value or `data_generation_clients` will cause the generation of a different dataset. Must be an integer.
* `integration_ratios` - A dictionary containing a key per integration. Each integration in turn has a configuration object. This object includes a `corpora` dictionary, containing the ratios of the source corpora to use for this integration in the generated corpus. The keys represent the corpus names and the values the ratios. See [Ratios](#ratios) for further details.
* `exclude_properties` - The list of fields to remove from the source corpora when generating a corpus. The keys represent the corpus names and the values a list of fields to remove per corpus. Only root fields can currently be removed from the JSON.

### Indexing Parameters

* `number_of_shards` (default: 1) - The number of primary shards to set per Data Stream. The same value is used for all Data Streams.
* `number_of_replicas` (default: 1) - The number of replicas to set per Data Stream. The same value is used for all Data Streams.
* `refresh_interval` (default: unset) - The Data Stream refresh interval. It is unset by default to use the Elasticsearch default refresh interval.
* `bulk_indexing_clients` (default: 8) - The number of clients issuing indexing requests.
* `runtime_indexing_clients`(default: bulk_indexing_clients) - for the simoutaneous indexing and querying challenge (`logging-indexing-querying`) this allows a different number of clients to be used in runtime vs the initial bulk load.
* `bulk_size` (default: 1000) - The number of documents to send per indexing request.
* `runtime_bulk_size` (default: bulk_size) - The number of documents to send per indexing request during the runtime phase of `logging-indexing-querying`challenge.
* `throttle_indexing` (default: `false`) - Whether indexing should be throttled to the rate determined by `raw_data_volume_per_day`, assuming a uniform distribution of data, or whether indexing should go as fast as possible. 
* `disable_pipelines` (default: `false`) - Prevent installing ingest node pipelines. This parameter is experimental and is to be used with indexing-only challenges.
* `initial_indices_count` (default: 0) - Number of initial indices to create, each containing `100` auditbeat style documents. Parameter is applicable in [many-shards-quantitative challenge](#many-shards-quantitative-many-shards-quantitative) and in [many-shards-snapshots challenge](#many-shards-snapshots-many-shards-snapshots).
* `ingest_percentage` (default: 100) - The percentage of data to be ingested.
* `index_mode` (default: unset): What index mode to use. Accepted values: `standard` and `logs`. 
* `force_merge_max_num_segments` (default: unset): An integer specifying the max amount of segments the force-merge operation should use. Only supported in `logging-querying` track.
* `include_non_serverless_index_settings` (default: true for non-serverless clusters, false for serverless clusters): Whether to include non-serverless index settings.
* `codec` (default: unset): Configured the `index.codec` index setting, which controls how stored fields get stored / compressed.

### Querying parameters

* `workflow_time_interval` (default: 30) - The mean time between executions of a workflow. A Poisson process resulting in an exponentially distributed delay.
* `think_time_interval` (default: 4) - The mean time between the execution of actions of a workflow. A Poisson process resulting in an exponentially distributed delay. Users of the track shouldn't need to modify this parameter.
* `query_warmup_time_period` (default: 120) - Warmup time for queries before measurements are recorded.
* `query_time_period` (default: 900) - The period for which queries should be issued. This only applies to challenges where no concurrent indexing is occurring. If concurrent indexing is occurring, querying will stop once this completes.
* `random_seed` (default: 13) - Integer used to determine the order of query execution. The interval between workflow executions, as well as the actions within them, is based on an exponentially distributed random variable. Seeding this process ensures execution is deterministic across different executions.
* `query_min_date` (default: `2020-01-01`) - Minimum datetime to execute queries over (such as yyyy-MM-dd or yyyy-MM-ddThh:mm:ss.zzzZ). Affects ranges and date_histograms.  Must be less than `query_max_date` (or `query_max_date_start`).
* `query_max_date` (default: `2020-01-02`) - Maximum datetime to execute queries over (such as yyyy-MM-dd or yyyy-MM-ddThh:mm:ss.zzzZ). Affects ranges and date_histograms. Cannot be configured when `query_max_date_start` is also defined.
* `search_clients` (default: 1) - The number of clients per workflow that issue search requests.
* `query_max_date_start` (optional) - Maximum datetime to execute queries over, at the beginning of a query workflow task. Increments with the time elapsed as the benchmark executes. Cannot be configured when `query_max_date` is also defined.
* `query_average_interval` (optional) - Average time interval for queries to use. If unset, we use the durations and intervals set in the original action definitions.
* `query_request_params` (optional) - A map of query parameters that will be used with any querying.
* `query_workflows` (optional) - A list of workflows to execute. By default, all workflows are used.
* `include_esql_queries` (default: true for non-serverless clusters, false for serverless clusters): Whether to include ESQL and ESQL-related queries.

### Snapshot parameters
* `snapshot_counts` (default: `100`) - Specifies the number of back to back snapshots to issue and wait until all have completed. Applicable only to [many-shards-snapshots challenge](#many-shards-snapshots-many-shards-snapshots).
* `snapshot_repo_name` (default: `logging`) - Snapshot repository name.
* `snapshot_repo_type` (default: `s3`) - Other valid choices can be `gcs` and `azure`.
* `snapshot_repo_settings` (default: 
```
{
    "bucket": snapshot_bucket | default("test-bucket"),
    "client": "default",
    "base_path": snapshot_base_path | default("observability/logging"),
    "max_snapshot_bytes_per_sec": -1,
    "readonly": snapshot_repo_readonly | default(false)
}
```
Setting that can also be set with separate parameters is `snapshot_bucket`, `snapshot_base_path` and `snapshot_repo_readonly`
* `snapshot_name` (default: `logging-test`) Snapshot name when creating or to recover. Used as a prefix in case more than one snapshot is taken.
* `restore_data_streams` (default: `logs-*`) Specifies data streams for `restore-snapshot` and `create-snapshot` operations.
* `snapshot_metadata` (default: `{}`) Metadata to set when creating a snapshot. Used in `create-snapshot` operation.

## Available Challenges

The following challenges are currently subject to change.

### Challenges that can be used as a setup prior to other challenges

#### logging-snapshot-restore

Restores snapshots specified with [snapshot parameters](#snapshot-parameters) prior to testing. Example can be used before running [Logging Querying challenge](#logging-querying-logging-querying).

#### logging-snapshot-mount

Mounts searchable snapshots as partial indices to test the frozen tier.

#### logging-snapshot

Performs a snapshot of the cluster.

### Logging Disk Usage (logging-disk-usage)

This challenge aims to establish the required storage in Elasticsearch for every GB of raw data. This "indexing factor" can be used to estimate disk space requirements for Elasticsearch from raw data. This challenge can be used for any of the use cases supported by this track.

This challenge indexes the specified volumes unthrottled. Statistics on each Data Stream are captured on completion of indexing.

No querying is performed as part of this challenge.

Advanced users may wish to modify the dataset composition as detailed [Changing the Datasets](#changing-the-datasets).

### Logging Indexing (logging-indexing)

This challenge aims to establish the indexing throughput that can be supported by an Elasticsearch cluster. This challenge indexes the specified volume. No queries are issued. Index throttling can be enabled via the parameter `bulk_indexing_clients`.

In order to optimise indexing throughput, users may wish to consider modifying the `bulk_indexing_clients` and `bulk_size`.

### Logging Querying (logging-querying)

This challenge simulates Kibana load via so-called workflows. Workflows execute concurrently at random intervals, and each workflow executes their actions sequentially until completion. An exponentially distributed random delay occurs between each action - the mean of this distribution can be controlled through the parameter `think_time_interval`. This simulates the user pausing and thinking between actions. A random delay (also exponentially distributed and controlled via a parameter `workflow_time_interval`) occurs between executing workflows. This is the main parameter users should use to control individual levels of user activity. Queries will be issued for the period specified by the parameter `query_time_period`. No indexing will occur.

Users of this track may use this challenge to execute queries on an existing index for which bulk indexing has completed e.g. after using the challenge `#Logging Indexing`. 

Be aware that queries containing time ranges will respect the `start_date` specified for the track. i.e. When a query is executed, any date ranges will be modified and assume the current time is the `start_date` + `time since challenge executed`. We recommend using absolute dates where possible and ensuring you have data for the entire time period of execution given that this is constantly moving forward. Any relative dates will be resolved on track initialization.

### Logging Indexing and Querying (logging-indexing-querying)

This challenge executes indexing and querying concurrently. Queries will be issued until indexing completes. Indexing can either be throttled or unthrottled. 

Note: If the indexing load is higher than the cluster can support, a time lag will start to occur on the indexed documents. This may result in queries returning with no hits as the expected data has yet to be indexed.

### Many Shards Snapshots (many-shards-snapshots)

This benchmarks aims to track performance and stability improvements related to snapshots in use cases with a high shard count. The challenge creates and indexes into initial set of indices (count controlled by `data.initial.indices` param); each index receives 100 auditbeat-like documents. Issues a number of sequential create snapshot requests (non blocking, using `wait_for_completion=false`), configurable via `snapshot_counts`. Waits until all snapshots have completed. The performance can be evaluated by the `service_time` of the `wait-for-snapshots` task.

Note that this challenge requires you to be able to successfully create a snapshot repository using the `snapshot_repo_type`, and `many_shards_snapshot_repo_settings` track parameters.

### Many Shards Quantitative (many-shards-quantitative)

This challenge aims to get more specific numbers of what we can support in terms of indices count. It creates initial 
set of indices as before and then index to small set of data streams. These data streams will almost never
rollover (rollover based on size with 100gb as `max_size`). This is supposed to be run with multiple values of
`initial_indices_count` parameter (0k, 5k, 10k, 20k, 25k, 30k etc), to find when we observe slowdown of more than 20% 
compared baseline or there are other symptoms that we are in bad shape (excessive GC collection etc).

Users of this track may use this challenge as base for nightly tests in regard to indices count (`initial_indices_count=20k`
is good start point)

### Cross Cluster Search + Cross Cluster Replication

A common architecture for geographically dispersed Logging/o11y use cases is to use the Cross Cluster Search (CCS) functionality to fan out searches from a central (local) cluster to many 'remote' clusters. This challenge aims to benchmark the query performance of the various workflows as they are performed through CCS.

All 'remote' clusters are configured on the 'local' cluster with the `remote*` prefix, this is achieved by using the `default` cluster specified in via `--target-hosts` as the 'local' cluster, and all others as 'remote' clusters.

For example, the below `esrally` invocation would setup the cluster hosted in `us-east-1` as the 'local' cluster, and the `us-west-1` and `ap-southeast-1` clusters as `remote*` prefixed clusters. There is no limit on the number of 'remote' clusters that can be configured, but there can only be one 'local' cluster from which searches are executed.
```
esrally race --track=elastic/logs --client-options='{"default": {"basic_auth_user": "elastic", "basic_auth_password": "changeme"}, "us-west-1-cluster": {[...]}, "ap-southeast-1-cluster": {[...]}}' --target-hosts='{"default":{"https://elasticsearch-us-east-1:9200"}, "us-west-1-cluster":{"https://elasticsearch-us-west-1:9200}, "ap-southeast-1-cluster": {"https://elasticsearch-ap-southeast-1"}}'
```

#### (cross-clusters-search-and-replication)

Indexes logs to the default (local) cluster, then replicates to all other clusters specified in 'target-hosts' using Cross Cluster Replication (CCR), finally searching across all clusters via Cross Cluster Search (CCS).

Note that this challenge requires _all_ clusters to have the CCR feature licensed.

#### (cross-clusters-search-and-snapshot)

Indexes logs to the default (local) cluster, snapshots the resulting data streams and restores the snapshot across all other clusters specified in 'target-hosts', finally searching across all clusters via Cross Cluster Search (CCS).

Note that this challenge requires you to be able to successfully create a snapshot repository using the `snapshot_repo_name`, `snapshot_repo_type`, and `snapshot_repo_settings` track parameters.

### Parameters specific to datastream-autosharding challenge

This challenge is intended for serverless data streams auto sharding testing. It consists of configurable number of steps provided with array parameters.
Note: `include_target_throughput` parameter is ignored in this challenge.

* `as_clients` (default: [8,16,32]): An array with the number of indexing clients to be used in each step.
* `as_warmup_time_periods` (default: [300,300,300]): An array with warm-up time period, in seconds, of every step.
* `as_time_periods` (default: [300,300,300]): An array with time period, in seconds, of every step.
* `as_target_throughputs` (default: [2,4,8]): An array with target throughput of each step, expressed in requests/s. Please use `bulk_size` parameter to translate this into docs/s. Target throughput is not configured if the values specified in this array are negative.
* `ds_autosharding_excludes` (default: []) a list of data stream name patterns to exclude from auto sharding.
* `ds_autosharding_increase_cooldown` (default: "270s") A time value indicating the amount of time to cooldown before increasing the number of shards.
* `ds_autosharding_decrease_cooldown` (default: "3d") A time value indicating the amount of time to cooldown before decreasing the number of shards.
* `ds_autosharding_min_threads` (default: 2) The minimum number of write threads in the auto *scaling* function.
* `ds_autosharding_max_threads` (default: 32) The maximum number of write threads in the auto *scaling* function.
* `dsl_poll_interval` (default: "5m") A time value indicating the interval data stream lifecycle runs at. This is relevant in the context of auto sharding as data stream lifecycle periodically triggers the rollover operations that will recalcualte and implement the (auto)sharding scheme.

### Categorize Text (categorize-text)

Runs the categorize-text aggregation with varying values of shard-size and with/without the use of a sampler
aggregation. The challenge targets a specific set of indices by way of an index alias.

### Reindex Data Stream (logging-reindex-data-stream)

Restores a data stream from 7.x snapshots and reindexes all indices into version 8.x. 
The snapshot parameters are used to define the correct snapshot, with `restore_data_streams` being the data stream to reindex.
This challenge also uses the following task specific parameters:
* `reindex_max_concurrent_indices` (default: 1) The maximum number of data stream backing indices that will be reindexed at the same time.
* `reindex_max_requests_per_second` (default: 1000) The average maximum number of documents that will be reindexed per second, per backing index.

## Changing the Datasets

The generated dataset is influenced by 2 key configurations:

* Ratios of each corpus to use in the generate data
* Fields to remove from the original corpora documents

The default ratios and list of fields to remove are revised over time, but should be considered to be authoritative and based on Elastic's current understanding of what constitutes a representative dataset for a specific use case. Further details are given below.

The following is for advanced users only and should be done in exceptional circumstances.

### Ratios

By default, the track generates a dataset by sampling the source corpora randomly according to defined ratios. These ratios can be changed through the parameter `integration_ratios`. 

This parameter must be passed as a dictionary where the top level keys represent the integration names. Each integration in turn has its own dictionary with a `corpora` object.  This object describes the corpora associated with the integration as well as the ratios to use when generating the dataset.  The ratios values are recalculated to a percentage of the total data generated. Changing this value requires the user to understand which corpora are associated with which integrations - this thus represents an advanced use case.

As an example, consider the following for the integrations `kafka` and `nginx`:

```
{
    "kafka": {
      "corpora": {
        "kafka-logs": 0.25
      }
    }
    "nginx": {
      "corpora": {
        "nginx-access-logs": 0.25,
        "nginx-access-logs-2": 0.1,
        "nginx-error-logs": 0.1,
        "nginx-error-logs-2": 0.3
      }
    }
}
```

Note how in this case, the ratios associated with the corpora sum to 1 i.e. `0.25+0.25+0.1+0.1+0.3 = 1.0` allowing for easier calculation of the data distribution but this is not required. For cases when all integration rations do not add up to 1, [data_generator.py processor](https://github.com/elastic/rally-tracks/blob/e86cbff0666eb3c6a62afe109cb90581fc69f8b0/elastic/shared/track_processors/data_generator.py#LL252C15-L252C15) will recalculate the ratios.  


The parameter `integration_ratios` is best set via a track parameter file as described here [here](https://esrally.readthedocs.io/en/stable/command_line_reference.html#track-params). 

### Remove Fields

The original corpora datasets are very verbose. We therefore remove some fields to ensure datasets are representative for a use case. The list of fields to remove can be changed through the parameter `exclude_properties`. This parameter must be passed as a dictionary where the keys represent the corpus names and the values a list of fields to remove per corpus. Only root fields can currently be removed (`.` notation for sub fields is currently not supported). This parameter is best set via track parameter file as described here [here](https://esrally.readthedocs.io/en/stable/command_line_reference.html#track-params).

## Extending and Adapting

This track can be used as it is, but was designed so that it would be easy to extend or modify it. The two directories `operations` and `challenges`, contain files with the standard components of this track that can be used as an example. The main `track.json` file will automatically load all files with a .json suffix from these directories. This makes it simple to add new operations and challenges without having to update or modify any of the original files.

## Elasticsearch Compatibility

Currently only Elasticsearch 7.9+ is supported due to the requirement for Data Streams and Composable Template support.

## Versioning Scheme

https://esrally.readthedocs.io/en/stable/track.html#track-repositories-branch-logic

## How to Contribute

If you want to contribute to this track, please ensure that it works against the main version of Elasticsearch (i.e. submit PRs against the master branch). We can then check whether it's feasible to backport the track to earlier Elasticsearch versions.

See all details in the [contributor guidelines](https://github.com/elastic/rally/blob/master/CONTRIBUTING.md).

## Running Tests

This track contains associated unit tests. In order to run them, please issue the following commands:

```
# only required once for the initial setup
make prereq
make install
# to run the tests
make test
```

An integration test suite is available and can be run with `make it`, which executes a smoke test and a query test.
For snapshot integration tests, specify a target S3 bucket which contains the desired snapshot(s) using `make snapshot_bucket=<your-bucket-here> snapshot-it`.

## FAQ

1. How much disk space do I need?
	
	Disk space is consumed by both the original downloaded corpora and the generated corpus.
		
	When specifying a `raw_data_volume_per_day` you are actually asking for the volume of raw data to simulate e.g. for log files, the volume of logs on disk. When a log message is converted to JSON it inherently increases its size due to the associated notation overhead. The Elastic agent adds further meta fields e.g. `host_name`, which cause this size to increase further. This "raw to JSON expansion factor" N, means that 1GB of raw data will equate to NGB of JSON on disk. Furthermore, this factor is different from different corpuses - as they have different meta fields and common enrichments. On average, we estimate this factor to be approximately 10x - but its subject to changes in the Elastic agent and the metadata enrichment the user chooses to enable at source. The parameter `max_generated_corpus_size` is therefore critical - this places an upper limit on the JSON data generated. In most cases this will be the limiting factor on data generation.
		
	Therefore, allow the sum of the following:
		
	* `max_total_download_gb` which defaults to `2 * num of corpus` (18 corpus currently) or `36gb` by default. At minimum `1gb` per corpus will be downloaded, irrespective of this value, requiring at least `18gb` of disk space. Note: `max_total_download_gb` will be rounded upto a multiple of the number of corpora e.g. `30` with be converted to `36`.
	* Allow `min((end_date - start_date) * raw_data_volume_per_day * 10, max_generated_corpus_size)` for generated. 
	
2. How much data will be sent to my cluster during indexing?
	
	Similar to data generation, the associated expansion of converting raw messages to JSON means that more data will be sent to Elasticsearch then the value of `raw_data_volume_per_day` * `(end_date - start_date)`. We estimate this expansion factor to be around 10x based on the default corpus ratios. This value is highly variable across different corpora - if you modify the corpus ratios the expansion factor may therefore increase or decrease accordingly.
	
3. Why is more data generated and sent than specified by `raw_data_volume_per_day` * `(end_date - start_date)`? 

	See question (2)

4. Can data be indexed more than once? Do I need to think about duplication?
	
	Duplication in data has the potential to cause higher levels of index compression in Elasticsearch than would be experienced in real world cases. To ensure testing is as accurate as possible we aim to minimise this effect but incorrect track usage can cause it to occur.
	 
	Data can occur in several stages of the track, most of which you can eliminate with sufficient disk resources:
	
	- Prior to indexing this track uses downloaded data for each corpus to generate a file with the specified corpus ratios. The volume of data downloaded can be limited by the parameter `max_total_download_gb`. This volume is shared equally across the corpora. A user can intentionally limit the downloaded volume to conserve disk space. If they inturn generate a file which requires more data for a corpus than has been downloaded, the track will reuse the downloaded source data - effectively causing duplication of documents in the generated file. At which point this occurs is difficult to predict - it will depend on the `max_total_download_gb`, corpus ratios and volume of data requested for generation (approximately `min(raw_data_volume_per_day * (end_date - start_date) * 10, max_generated_corpus_size)`. For very large generation sizes data will be inevitably be reused i.e. you will exhaust the available download corpus datasets. As a rule of thumb, we recommended setting `max_total_download_gb` to approximately `min(raw_data_volume_per_day * (end_date - start_date) * 10, max_generated_corpus_size) * 2.0` (assuming default corpus ratios).
	
	- Users can limit the size of the generated file using the parameter `max_generated_corpus_size`, in order to conserve disk space. Should this value be less than the required data needing indexing, the track will reuse the generated data - looping over it and inturn causing data duplication in Elasticsearch. The duplication caused by this behaviour converges to 0 as `max_generated_corpus_size` approaches approximately `raw_data_volume_per_day * (end_date - start_date) * 10` (assuming default corpus ratios).
	
5. How do I create a scenario where data is bulk loaded, and once sufficient volume is available, before querying and indexing occurs concurrently?


## License

This software is licensed under the Apache License, version 2 ("ALv2"), quoted below.

Copyright 2015-2020 Elasticsearch [https://www.elastic.co](https://www.elastic.co)

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.




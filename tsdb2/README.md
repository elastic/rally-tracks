## TSDB k8s query track

This track main goal is keeping track of the performance of common k8s integration search requests.
The queries, index templates and corpus data try to match production as close as possible.

Queries used in this track:
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

This track contains templates for these 10 most common queries for this integration.
Each of these queries is executed 3 times. First with last 15 minutes filter, then last 2 hours filter  and finally with a last 24 hour interval. In case a `date_histogram` is used in the query template then each of this variation uses a different interval. A fixed interval of 30 seconds, 1 minute and 30 minutes repectively.

The k8s visualizations that run these queries don't run very often or under a high query load.
Often these visualizations are loaded and then some time later re-loaded. This triggers the
shards of the k8s pod and container data streams to go search-idle. However indexing always
happen in the background. When shards become search-active again, a refresh need to occur
as part of the search request. This track is designed to emulate this runtime behaviour.
This is done by concurrently indexing while the searches are ran. By lowering the `index.search.idle.after` setting from 30s (which is the default) to 1s. And force fully reducing the query load, so that one search gets executed every 3 seconds.

[describe how data is generated]

### Parameters

This track allows to overwrite the following parameters using `--track-params`:

* `bulk_size` (default: 10000)
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `force_merge_max_num_segments` (default: unset): An integer specifying the max amount of segments the force-merge operation should use.
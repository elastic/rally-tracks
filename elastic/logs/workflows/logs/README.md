Queries in this folder represent a user using the logs solution in Kibana. 
Specifically this involves executing the following steps:

1. Opening the logs solution for the `now-24h` to `now`. Default index pattern is `logs-*`.
    Note: configured to include fields `host.ip`, `host.name`, `container.name`, `cloud.provider`, `cloud.machine.type` 
    and `cloud.region`. Queries should target `logs-*` pattern.
2. Search for `java.lang.NullPointerException`
3. Highlight `java.lang.NullPointerException`
4. Search for `googlebigquery`
5. Highlight `googlebigquery`
6. Start Streaming
7. Allow to stream for 60 seconds, before stopping streaming
8. Search for `*RejectedExecutionException*`
9. Click to start of timeline - so `Last 1 day` is applied
10. Filter to `host.name: infra-filebeat-qkrp7`


THIS WORKFLOW IS PENDING IMPLEMENTATION OF 
[DATE RANGE AGGREGATION](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-daterange-aggregation.html)
AND [SEARCH AFTER](https://www.elastic.co/guide/en/elasticsearch/reference/7.10/paginate-search-results.html#search-after).
Support for epoch in date range queries is also required.
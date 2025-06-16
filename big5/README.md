## Big5 Rally Track

The "Big5" track focuses on five essential areas in Elasticsearch performance and querying:

1. Text Querying:

   Free text search is vital for databases due to its flexibility, ease of use, and ability to quickly filter data. It allows users to input natural language queries, eliminating the need for complex query languages and making data retrieval more intuitive. With free text search, users can find information using familiar terms, such as names, email addresses, or user IDs, without requiring knowledge about the underlying schema. It is particularly useful for handling unstructured data, supporting partial matches, and facilitating data exploration.

2. Sorting:

   Sorting is a process of arranging data in a particular order, such as alphabetical, numerical, or chronological. The sort query in Elasticsearch is useful for organizing search results based on specific criteria, ensuring that the most relevant results are presented to users. It is a vital feature that enhances the user experience and improves the overall effectiveness of the search process.

   In the context of observability and security, in which signals from multiple systems are correlated, sorting is a crucial operation. By sorting results based on timestamp, metrics, or any other relevant field, analysts can more efficiently identify issues, security threats, or correlations within the data. With this information, it becomes easier to identify patterns, trends, and insights that can inform business decisions to protect your data and ensure uptime.

3. Date Histogram:

   The date histogram aggregation in Elasticsearch is useful for aggregating and analyzing time-based data by dividing it into intervals, or buckets. This capability allows users to visualize and better understand trends, patterns, and anomalies over time.

4. Range Queries:

   The range query in Elasticsearch is useful for filtering search results based on a specific range of values in a given field. This capability allows users to narrow down their search results and find more relevant information quickly.

5. Terms Aggregation:

   Terms allow users to dynamically build into buckets to source based on aggregation values. These can be 100s or 1000s of unique terms that get returned individually or in composite aggregations. Larger size values use more memory and compute to push the aggregations through.


### Data Document Structure

Depending on the parameters provided, the data set can become very large(The full dataset is around 1TB). Ensure that you have enough free disk space to store the data in this directory.

Below is the expected structure of the documents:

```json
{
    "message": "2023-04-30T21:48:56.160Z Apr 30 21:48:56 ip-66-221-134-40 journal: donkey glazer fly shark whip servant thornfalcon",
    "process": {
        "name": "journal"
    },
    "aws.cloudwatch": {
        "ingestion_time": "2023-04-30T21:48:56.160Z",
        "log_group": "/var/log/messages",
        "log_stream": "luckcrafter"
    },
    "tags": [
        "preserve_original_event"
    ],
    "meta": {
        "file": "2023-01-02/1682891301-gotext.ndjson.gz"
    },
    "cloud": {
        "region": "eu-central-1"
    },
    "@timestamp": "2023-01-02T22:02:34.000Z",
    "input": {
        "type": "aws-cloudwatch"
    },
    "metrics": {
        "tmin": 849,
        "size": 1981
    },
    "log.file.path": "/var/log/messages/luckcrafter",
    "event": {
        "id": "sunsetmark",
        "dataset": "generic",
        "ingested": "2023-07-20T03:36:30.223806Z"
    },
    "agent": {
        "id": "c315dc22-3ea6-44dc-8d56-fd02f675367b",
        "name": "fancydancer",
        "ephemeral_id": "c315dc22-3ea6-44dc-8d56-fd02f675367b",
        "type": "filebeat",
        "version": "8.8.0"
    }
}
```

### Track Parameters

The following parameters are available:

* `number_of_shards` (default: 1) - The number of index primary shards.
* `number_of_replicas` (default: 0) - The number of replica shards per primary.
* `bulk_size` (default: 500) - The bulk size in number of documents.
* `bulk_indexing_clients` (default: 1) - The number of clients issuing indexing requests.
* `ingest_percentage` (default: 100) - A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `target_opensearch` (default: false) - Whether the target is an OpenSearch cluster
* `warmup_iterations` (default: 100) - Number of iterations that each client should execute to warmup the benchmark candidate.
* `iterations` (default: 1000) - Number of measurement iterations that each client executes.

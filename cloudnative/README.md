## Cloudnative Track

This data is extracted from a real Kubernetes cluster which was configured to send logs and metrics to Elastic Cloud.
System and kubernetes integration was enabled and elastic agent was used to send data to Elastic Cloud.

Extraction of data-streams and indexes from line Elastic Cloud was done with the help of rally `create-index`

Modifications:
* Change number of shard replicas to zero in all indices eg. `"number_of_replicas": "{{number_of_replicas | default(0)}}"`
*  For the query_aggregation operation we have defined the time limits of the query: 
   * `"gte" : "2022-04-22T07:00:00.886Z"`: Timestamp that defines the minimum time for task `query_aggregation`. It is aligned with specific corpora data. To be changed in case new data are provided.
   * `"lte" : "2022-11-22T07:00:33.886Z"`: Timestamp that defines the minimum time for task `query_aggregation`. It is aligned with specific corpora data. To be changed in case new data are provided

### Example document

```json
{
  "template": {
    "settings": {
      "index": {
        "lifecycle": {
          "name": "metrics"
        },
        "codec": "best_compression",
        "routing": {
          "allocation": {
            "include": {
              "_tier_preference": "data_hot"
            }
          }
        },
        "query": {
          "default_field": [
            "message"
          ]
        }
      }
    },
    "mappings": {
      "dynamic_templates": [
        {
          "match_ip": {
            "match": "ip",
            "match_mapping_type": "string",
            "mapping": {
              "type": "ip"
            }
          }
        },
        {
          "match_message": {
            "match": "message",
            "match_mapping_type": "string",
            "mapping": {
              "type": "match_only_text"
            }
          }
        },
        {
          "strings_as_keyword": {
            "match_mapping_type": "string",
            "mapping": {
              "ignore_above": 1024,
              "type": "keyword"
            }
          }
        }
      ],
      "date_detection": false,
      "properties": {
        "@timestamp": {
          "type": "date"
        },
        "data_stream": {
          "properties": {
            "dataset": {
              "type": "constant_keyword"
            },
            "namespace": {
              "type": "constant_keyword"
            },
            "type": {
              "type": "constant_keyword",
              "value": "metrics"
            }
          }
        },
        "ecs": {
          "properties": {
            "version": {
              "type": "keyword",
              "ignore_above": 1024
            }
          }
        },
        "host": {
          "type": "object"
        }
      }
    },
    "aliases": {}
  }
}
```


### Fetching new data

This data comes from a real cluster that has been deployed with Terraform of [k8s-integration-infra](https://github.com/elastic/k8s-integration-infra/tree/main/infra)

### Parameters

This track allows to overwrite the following parameters using `--track-params`:

* `bulk_size` (default: 10000)
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `index_settings` (default{}): A list of index settings. Index settings defined elsewhere (e.g. number_of_replicas) need to be overridden explicitly.
* `recency `(default: 0): A number between 0 and 1 that defines whether to bias towards more recent ids when simulating conflicts. See the Rally docs for the full definition of this parameter. This requires to run the respective challenge.
* `number_of_replicas` (default: 0)
* `number_of_shards` (default: 5)
* `ingest_percentage `(default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `conflicts` (default: "random"): Type of id conflicts to simulate. Valid values are: 'sequential' (A document id is replaced with a document id with a sequentially increasing id), 'random' (A document id is replaced with a document id with a random other id).
* `conflict_probability` (default: 25): A number between 0 and 100 that defines the probability of id conflicts. This requires to run the respective challenge. Combining conflicts=sequential and conflict-probability=0 makes Rally generate index ids by itself, instead of relying on Elasticsearch's automatic id generation <https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-index_.html#_automatic_id_generation>_.
* `on_conflict` (default: "index"): Whether to use an "index" or an "update" action when simulating an id conflict.
* `cluster_health` (default: "green"): The minimum required cluster health.
* `error_level` (default: "non-fatal"): Available for bulk operations only to specify ignore-response-error-level.


### License

All articles that are included are licensed as CC-BY-NC-ND (https://creativecommons.org/licenses/by-nc-nd/4.0/)

This data set is licensed under the same terms. Please refer to https://creativecommons.org/licenses/by-nc-nd/4.0/ for details.

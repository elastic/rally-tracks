## Cloudnative Track

This data is extracted from a real Kubernetes cluster which was configured to send logs and metrics to Elastic Cloud.
System and kubernetes integration was enabled and elastic agent was used to send data to Elastic Cloud.

Extraction of data-streams and indexes from line Elastic Cloud was done with the help of rally `create-index`

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


### License

All articles that are included are licensed as CC-BY-NC-ND (https://creativecommons.org/licenses/by-nc-nd/4.0/)

This data set is licensed under the same terms. Please refer to https://creativecommons.org/licenses/by-nc-nd/4.0/ for details.

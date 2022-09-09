## Cloudnative Track

This track is extracted from a real Kubernetes cluster which was configured to send logs and metrics to Elastic Cloud.
System and kubernetes integrations were enabled and elastic agent used to send data to Elastic Cloud.

Extraction of data-streams and indexes from Elastic Cloud was done with the help of rally `create-index`
After auto-extraction with rally tool following modification needed in the indices:
* Change number of shard replicas to zero in all indices eg. `"number_of_replicas": "{{number_of_replicas | default(0)}}"`

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
>Reach @elastic/obs-cloudnative-monitoring team for access


#### Extraction of data and mappings

Corpora data of the specific data with their respective mappings were extracted with following command:

```bash
esrally create-track --track=test --target-hosts=<DNS-ELASTIC-STACK>:9200 --client-options="use_ssl:true,verify_certs:false,ca_certs:false,basic_auth_user:'elastic',basic_auth_password:'<REDACTED>'" --datastreams="metrics-*, logs-*" --output-path=~/tracks
```

### Running Track for different scenarios

#### For _Source:
Run Track as follows:
```
esrally race --distribution-version=8.3.0 --track-path=cloudnative --runtime-jdk=bundled --kill-running-processes --track-params="synthetic_source:false,source_enabled:true"
```

We also advise to use `--telemetry disk-usage-stats` to evaluate the disk usage performance

#### For synthetics

Edit `~/.rally/rally.ini`

```bash
[distributions]
in_house_snapshot.url = https://snapshots.elastic.co/8.4.0-0384b1d2/downloads/elasticsearch/elasticsearch-8.4.0-SNAPSHOT-darwin-x86_64.tar.gz
in_house_snapshot.cache = true
```

> Find appropriate image for your test machine in https://artifacts-api.elastic.co/v1/versions/8.4-SNAPSHOT/builds/latest

Run Track as follows:

```bash
esrally race --distribution-repository=in_house_snapshot --distribution-version=8.4.0-SNAPSHOT --track-path=cloudnative --kill-running-processes --track-params="synthetic_source:true,source_enabled:true"
```

We also advise to use `--telemetry disk-usage-stats` to evaluate the disk usage performance

#### For TSDB 
This track can not be used as it is to evaluate the TSDB feature. Initial extraction was done on a cluster where TSDB was not configured. Data need to be extracted from a pre-configured Kubernetes cluster where TSDB feature will be enabled  before hand.

### Parameters

This track allows to overwrite the following parameters using `--track-params`:

* `bulk_size` (default: 1000)
* `bulk_indexing_clients` (default: 5): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `index_settings` (default{}): A list of index settings. Index settings defined elsewhere (e.g. number_of_replicas) need to be overridden explicitly.
* `recency `(default: 0): A number between 0 and 1 that defines whether to bias towards more recent ids when simulating conflicts. See the Rally docs for the full definition of this parameter. This requires to run the respective challenge.
* `number_of_replicas` (default: 0)
* `number_of_shards` (default: 1)
* `conflicts` (default: "random"): Type of id conflicts to simulate. Valid values are: 'sequential' (A document id is replaced with a document id with a sequentially increasing id), 'random' (A document id is replaced with a document id with a random other id).
* `conflict_probability` (default: 25): A number between 0 and 100 that defines the probability of id conflicts. This requires to run the respective challenge. Combining conflicts=sequential and conflict-probability=0 makes Rally generate index ids by itself, instead of relying on Elasticsearch's automatic id generation <https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-index_.html#_automatic_id_generation>_.
* `on_conflict` (default: "index"): Whether to use an "index" or an "update" action when simulating an id conflict.
* `cluster_health` (default: "green"): The minimum required cluster health.
* `error_level` (default: "non-fatal"): Available for bulk operations only to specify ignore-response-error-level.
* `synthetic_source` (default: false): Boolean to enable synthetic _source
* `source_enabled` (default: false): A boolean defining whether the _source field is stored in the index.


### License

All articles that are included are licensed as CC-BY-NC-ND (https://creativecommons.org/licenses/by-nc-nd/4.0/)

This data set is licensed under the same terms. Please refer to https://creativecommons.org/licenses/by-nc-nd/4.0/ for details.

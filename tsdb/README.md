## TSDB Track

This data is anonymized monitoring data from elastic-apps designed to test
our TSDB project. TSDB support is being actively developed in Elasticsearch
right now so it's best to run this track only against Elasticsearch's
master branch.

TSDB needs us to be careful how we anonymize. Too much randomization and TSDB
can no longer do its job identifying time series and metrics and rates of
change. Too little and everyone knows all the software we run. We mostly err
towards openness here, but with a dash of paranoia.


### Example document

```
{
  "@timestamp": "2021-04-28T19:45:28.222Z",
  "kubernetes": {
    "namespace": "namespace0",
    "node": {"name": "gke-apps-node-name-0"},
    "pod": {"name": "pod-name-pod-name-0"},
    "volume": {
      "name": "volume-0",
      "fs": {
        "capacity": {"bytes": 7883960320},
        "used": {"bytes": 12288},
        "inodes": {"used": 9, "free": 1924786, "count": 1924795},
        "available": {"bytes": 7883948032}
      }
    }
  },
  "metricset": {"name": "volume","period": 10000},
  "fields": {"cluster": "elastic-apps"},
  "host": {"name": "gke-apps-host-name0"},
  "agent": {
    "id": "96db921d-d0a0-4d00-93b7-2b6cfc591bc3",
    "version": "7.6.2",
    "type": "metricbeat",
    "ephemeral_id": "c0aee896-0c67-45e4-ba76-68fcd6ec4cde",
    "hostname": "gke-apps-host-name-0"
  },
  "ecs": {"version": "1.4.0"},
  "service": {"address": "service-address-0","type": "kubernetes"},
  "event": {
    "dataset": "kubernetes.volume",
    "module": "kubernetes",
    "duration": 132588484
  }
}
```


### Fetching new data

This data comes from a private elastic-apps private k8s cluster. If you have
access to that cluster's logging then you can update the test data by
fetching raw, non-anonymized data from it's monitoring cluster with something
like elastic-dump. You want one document per line.

Now that you have the data, the goal is to get the anonymizer to run on the
entire dump in one go. But, in order to do that, let's slice out parts of the
file and make sure they can be processed first. Then we'll run them all at once.

First, let's tackle the documents with `message` fields. These are super diverse
and likely to fail on every new batch of data.
```
mkdir tmp
cd tmp

grep \"message\" ../data.json | split -l 100000
for file in x*; do
  echo $file
  python ../tsdb/_tools/anonymize.py < $file > /dev/null && rm $file
done
```

Some of the runs in the `for` loop are likely to fail. Those will leave files
around so you can fix the anonymizer and retry. We try to keep as many real
messages as we can without leaking too much information. So any new kind of
message will fail this process. Modify the script, redacting new message types
that come from the errors. Rerun the for loop above until it finishes without
error.

Now run the same process on documents without a message.

```
grep -v \"message\" ../data.json | split -l 100000
for file in x*; do
  echo $file
  python ../tsdb/_tools/anonymize.py < $file > /dev/null && rm $file
done
```

These are less likely to fail but there are more documents without messages
and any new failure will require a litte thought about whether the field it
found needs to be redacted or modified or passed through unchanged. Good luck.

Once all of those finish you should run the tool on the newly aquired data
from start to finish. You can't split the input data or the anonymizer won't
make consistent time series ids. Do something like:

```
cd ..
rm -rf tmp
python tsdb/_tools/anonymize.py < data.json > documents.json
```

Once that finishes you need to generate `documents-1k.json` for easy testing:
```
head -n 1000 documents.json > documents-1k.json
```

Now you'll need to make the `-sorted` variant. First install https://github.com/winebarrel/jlsort .
Then:
```
mkdir tmp
TMPDIR=tmp ~/Downloads/jlsort/target/release/jlsort -k '@timestamp' documents.json > documents-sorted.json
rm -rf tmp
head -n 1000 documents-sorted.json > documents-sorted-1k.json
```

Now zip everything up:
```
pbzip2 documents-1k.json
pbzip2 documents-sorted-1k.json
pbzip2 documents.json
pbzip2 documents-sorted.json
```

Now upload all of that to the AWS location from `track.json`.

### Parameters

This track allows to overwrite the following parameters using `--track-params`:

* `bulk_size` (default: 10000)
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `number_of_replicas` (default: 0)
* `number_of_shards` (default: 1)
* `force_merge_max_num_segments` (default: unset): An integer specifying the max amount of segments the force-merge operation should use.
* `source_enabled` (default: true): A boolean defining whether the `_source` field is stored in the index.
* `index_mode` (default: time_series): Whether to make a standard index (`standard`) or time series index (`time_series`)
* `codec` (default: default): The codec to use compressing the index. `default` uses more space and less cpu. `best_compression` uses less space and more cpu.
* `ingest_order` (default: jumbled): Should the data be loaded in `sorted` order or a more `jumbled`, mostly random order.

### License

All articles that are included are licensed as CC-BY-NC-ND (https://creativecommons.org/licenses/by-nc-nd/4.0/)

This data set is licensed under the same terms. Please refer to https://creativecommons.org/licenses/by-nc-nd/4.0/ for details.

## TSDB Track

This data is anonymized monitoring data from elastic-apps designed to test
our TSDB project. TSDB support is being actively developed in Elasticsearch
right now so it's best to run this track only against Elasticsearch's
main branch.

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
python tsdb/_tools/anonymize.py < data.json > data-anonymized.json
```

Now you'll need to make the `-sorted` variant. First install https://github.com/winebarrel/jlsort .
Then:
```
mkdir tmp
TMPDIR=tmp ~/Downloads/jlsort/target/release/jlsort -k '@timestamp' data-anonymized.json > data-sorted.json
rm -rf tmp
```

Finally you'll also need a deduped version of the data in order to to support the `ingest_mode` that
benchmarks ingesting into a tsdb data stream (`data_stream`). Use the `dedupe.py` tool in the
`_tools` directory. This tool needs `data-sorted.json` as input via standard in and generates a
deduped variant via standard out.

```
cat data-sorted.json | dedupe.py > documents.json
```

The `dedupe.py` tool also generates other files started with `dupes-` prefix.
These files contain the duplicates that are filtered out of the lines being
redirected to standard out. These files can optionally be manually checked for
whether these files contain lines that are truely duplicates.

Also generate a `documents-1k.json` file for easy testing:
```
head -n 1000 documents-sorted-deduped.json > documents-sorted-deduped-1k.json
```

Now zip everything up:
```
pbzip2 documents-1k.json
pbzip2 documents.json
```

Now upload all of that to the AWS location from `track.json`.

### Generating the split16 corpus

By default, with N indexing clients Rally will split documents.json in N parts and bulk index from
them in parallel. As a result, by default ingest is not done in order, which makes TSDB sorting
appear more costly than it really is. To work around this issue, we rearrange the original corpora
by splitting it in 16 parts (the number of indexing clients we use in practice in benchmarks) so
that indexing is done in roughly order.

To generate that corpus, first split the data in 16 files:

```
_tools/split.py ~/.rally/benchmarks/data/tsdb/documents.json 16
```

Note that this is a destructive operation! It will drop up to 15 documents so that the resulting
file contains a number of documents that is a multiple of 16 to ensure that Rally will split the
file as expected.

Now generate a single file again out of the splits:

```
cat documents-split-0.json documents-split-1.json documents-split-2.json documents-split-3.json documents-split-4.json documents-split-5.json documents-split-6.json documents-split-7.json documents-split-8.json documents-split-9.json documents-split-10.json documents-split-11.json documents-split-12.json documents-split-13.json documents-split-14.json documents-split-15.json > documents-split16-v2.json
```

The versioning (v2 here) ensures that nobody will use an old version of that corpus by accident.

Finally, as shown above, you can now then generate the 1k documents version, run pbzip2 on both
versions and upload the two resulting files to AWS.


### Parameters

This track allows to overwrite the following parameters using `--track-params`:

* `bulk_size` (default: 10000)
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `number_of_replicas` (default: 0)
* `number_of_shards` (default: 1)
* `refresh_interval` (default not defined)
* `force_merge_max_num_segments` (default: unset): An integer specifying the max amount of segments the force-merge operation should use.
* `source_mode` (default: synthetic): Should the `_source` be `stored` to disk exactly as sent (the Elasticsearch default outside of TSDB mode), thrown away (`disabled`), or reconstructed on the fly (`synthetic`)
* `index_mode` (default: time_series): Whether to make a standard index (`standard`) or time series index (`time_series`)
* `codec` (default: default): The codec to use compressing the index. `default` uses more space and less cpu. `best_compression` uses less space and more cpu.
* `ingest_mode` (default: index) Should be `data_stream` to benchmark ingesting into a tsdb data stream.
* `corpus` (default: full) Should be `split16` to use a corpus split in 16 to be used with 16 indexing clients and index mostly in @timestamp order.

### License

All articles that are included are licensed as CC-BY-NC-ND (https://creativecommons.org/licenses/by-nc-nd/4.0/)

This data set is licensed under the same terms. Please refer to https://creativecommons.org/licenses/by-nc-nd/4.0/ for details.

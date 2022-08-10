# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import json
import os

import pytest
from esrally.exceptions import InvalidSyntax, DataError, TrackConfigError
from shared.parameter_sources.processed import ProcessedCorpusParamSource
from shared.utils.time import TimeParsingError
from tests.parameter_sources import StaticTrack


def test_corpus_read():
    cwd = os.path.dirname(__file__)
    test_track = StaticTrack(
        parameters={
            "track-id": "test_file_write",
            "end-date": "2020-09-01:00:00:00",
            "start-date": "2020-08-31:00:00:00",
            "raw-data-volume-per-day": "0.1MB",
        },
        generated_document_paths=[
            os.path.join(
                cwd, "resources", "processed_test", "test_corpus_read", "0.json"
            )
        ],
    )

    param_source = ProcessedCorpusParamSource(
        track=test_track,
        params={
            "time-format": "milliseconds",
            "profile": "fixed_interval",
            "bulk-size": 10,
        },
    )
    client_param_source = param_source.partition(partition_index=0, total_partitions=1)
    total_batches = 0
    while True:
        try:
            client_param_source.params()
            total_batches += 1
        except StopIteration:
            break
    assert total_batches == 1748


def test_corpus_read_changing_bulk_size():
    cwd = os.path.dirname(__file__)
    test_track = StaticTrack(
        parameters={
            "track-id": "test_file_write",
            "end-date": "2020-09-01:00:00:00",
            "start-date": "2020-08-31:00:00:00",
            "raw-data-volume-per-day": "0.1MB",
        },
        generated_document_paths=[
            os.path.join(
                cwd, "resources", "processed_test", "test_corpus_read", "0.json"
            )
        ],
    )

    param_source = ProcessedCorpusParamSource(
        track=test_track,
        params={
            "time-format": "milliseconds",
            "profile": "fixed_interval",
            "bulk-size": 10,
        },
    )
    client_param_source = param_source.partition(partition_index=0, total_partitions=1)
    for i in range(0, 10):
        docs = client_param_source.params()
        assert len(docs["body"]) == 20
    client_param_source.set_bulk_size(20)
    for i in range(0, 10):
        docs = client_param_source.params()
        assert len(docs["body"]) == 40


def test_raw_corpus_read():
    cwd = os.path.dirname(__file__)
    test_track = StaticTrack(
        parameters={
            "track-id": "test_file_write",
            "end-date": "2020-09-01:00:00:00",
            "start-date": "2020-08-31:00:00:00",
            "raw-data-volume-per-day": "0.1MB",
        },
        generated_document_paths=[
            os.path.join(
                cwd, "resources", "processed_test", "test_corpus_read", "0.json"
            )
        ],
    )

    param_source = ProcessedCorpusParamSource(
        track=test_track,
        params={
            "time-format": "milliseconds",
            "profile": "fixed_interval",
            "bulk-size": 10,
        },
    )
    client_param_source = param_source.partition(partition_index=0, total_partitions=1)
    total_batches = 0
    while True:
        try:
            client_param_source.params()
            total_batches += 1
        except StopIteration:
            break
    # (0.1 * 1024 * 1024)/6
    assert total_batches == 1748


def test_multi_client_corpus_read():
    cwd = os.path.dirname(__file__)
    test_track = StaticTrack(
        parameters={
            "track-id": "test_file_write",
            "start-date": "2020-08-31:00:00:00",
            "end-date": "2020-09-01:00:00:00",
            "raw-data-volume-per-day": "0.01MB",
            "random-seed": 13,
        },
        generated_document_paths=[
            os.path.join(
                cwd,
                "resources",
                "processed_test",
                "test_multi_client_corpus_read",
                "0.json",
            )
        ],
    )

    param_source = ProcessedCorpusParamSource(
        track=test_track,
        params={
            "time-format": "milliseconds",
            "profile": "fixed_interval",
            "bulk-size": 1,
        },
    )
    # 1000 docs in the file, we need 669 in total. 334 in the first, 335 in the second
    client_1_param_source = param_source.partition(
        partition_index=0, total_partitions=2
    )
    total_batches = 0
    total_docs = 0
    while True:
        try:
            batch = client_1_param_source.params()
            docs = batch["body"]
            total_docs += len(docs) / 2
            # confirm we get the 1st slice of docs, no id should be > 873
            for d, doc_s in enumerate(docs):
                if d % 2 == 1:
                    doc = json.loads(doc_s)
                    assert doc["id"] <= 500
            total_batches += 1
        except StopIteration:
            break
    assert total_docs == 874
    assert total_batches == 874
    client_2_param_source = param_source.partition(
        partition_index=1, total_partitions=2
    )
    total_batches = 0
    total_docs = 0
    # 1000 docs in the file, 2nd batch starts at 1000 and we need 873 docs
    while True:
        try:
            batch = client_2_param_source.params()
            docs = batch["body"]
            total_docs += len(docs) / 2
            # confirm we get the 2st slice of docs, no id should be < 1748
            for d, doc_s in enumerate(docs):
                if d % 2 == 1:
                    doc = json.loads(doc_s)
                    assert 500 <= doc["id"] <= 1000
            total_batches += 1
        except StopIteration:
            break
    assert total_docs == 874
    assert total_batches == 874


def test_timestamp_corpus_read():
    cwd = os.path.dirname(__file__)
    test_track = StaticTrack(
        parameters={
            "track-id": "test_file_write",
            "end-date": "2020-09-01:00:00:00",
            "start-date": "2020-08-31:00:00:00",
            # These have changed compared to create_test_track()
            "raw-data-volume-per-day": "0.0001MB",
            "random-seed": 13,
        },
        generated_document_paths=[
            os.path.join(
                cwd, "resources", "processed_test", "test_corpus_read", "0.json"
            )
        ],
    )

    param_source = ProcessedCorpusParamSource(
        track=test_track,
        params={
            "time-format": "milliseconds",
            "profile": "fixed_interval",
            "bulk-size": 1,
        },
    )
    client_param_source = param_source.partition(partition_index=0, total_partitions=1)
    timestamps = [
        "2020-08-31T00:12:26.435Z",
        "2020-08-31T01:32:26.435Z",
        "2020-08-31T02:52:26.435Z",
        "2020-08-31T04:12:26.435Z",
        "2020-08-31T05:32:26.435Z",
        "2020-08-31T06:52:26.435Z",
        "2020-08-31T08:12:26.435Z",
        "2020-08-31T09:32:26.435Z",
        "2020-08-31T10:52:26.435Z",
        "2020-08-31T12:12:26.435Z",
        "2020-08-31T13:32:26.435Z",
        "2020-08-31T14:52:26.435Z",
        "2020-08-31T16:12:26.435Z",
        "2020-08-31T17:32:26.435Z",
        "2020-08-31T18:52:26.435Z",
        "2020-08-31T20:12:26.435Z",
        "2020-08-31T21:32:26.435Z",
        "2020-08-31T22:52:26.435Z",
    ]

    doc_num = 0
    previous_timespan = 0
    while True:
        try:
            docs = client_param_source.params()
            # first event timespan will be 0
            assert client_param_source.event_time_span >= previous_timespan
            previous_timespan = client_param_source.event_time_span
            doc = json.loads(docs["body"][1])
            assert doc["@timestamp"] == timestamps[doc_num]
            doc_num += 1
        except StopIteration:
            break
    assert doc_num == 18


def test_timespan_corpus_read():
    cwd = os.path.dirname(__file__)
    test_track = StaticTrack(
        parameters={
            "track-id": "test_file_write",
            "start-date": "2020-08-31:00:00:00",
            "end-date": "2020-09-01:00:00:00",
            "raw-data-volume-per-day": "0.001MB",
            "random-seed": 13,
        },
        generated_document_paths=[
            os.path.join(
                cwd,
                "resources",
                "processed_test",
                "test_timespan_corpus_read",
                "0.json",
            )
        ],
    )

    param_source = ProcessedCorpusParamSource(
        track=test_track,
        params={
            "time-format": "milliseconds",
            "profile": "fixed_interval",
            "bulk-size": 175,
        },
    )
    client_param_source = param_source.partition(partition_index=0, total_partitions=1)
    batches = 0
    num_docs = 0
    # 1048.576 bytes raw to be indexed. 6 bytes per doc, so 1048.576/6 = 175 docs
    # batch size is 175 so 175/25 = 1 batch.
    while True:
        try:
            docs = client_param_source.params()
            size = len(docs["body"]) / 2
            assert size == 175
            num_docs += size
            # close to one day
            assert client_param_source.event_time_span == 85906.285764
            assert (
                json.loads(docs["body"][1])["message"]
                == "2020-08-31T00:01:16.123456Z dummy"
            )
            assert (
                json.loads(docs["body"][-1])["message"]
                == "2020-08-31T23:53:03.123456Z dummy"
            )
            batches += 1
        except StopIteration:
            break
    assert batches == 1
    assert num_docs == 175


def test_relative_date_range():
    cwd = os.path.dirname(__file__)
    test_track = StaticTrack(
        parameters={
            "track-id": "test_file_write",
            "start-date": "now-1h",
            "end-date": "now-30m",
            "raw-data-volume-per-day": "0.048MB",
            "random-seed": 13,
        },
        generated_document_paths=[
            os.path.join(
                cwd, "resources", "processed_test", "test_corpus_read", "0.json"
            )
        ],
    )

    param_source = ProcessedCorpusParamSource(
        track=test_track,
        params={
            "time-format": "milliseconds",
            "profile": "fixed_interval",
            "bulk-size": 1,
        },
    )
    client_param_source = param_source.partition(partition_index=0, total_partitions=1)

    doc_num = 0
    while True:
        try:
            docs = client_param_source.params()
            doc = docs["body"][1]
            doc_num += 1
        except StopIteration:
            break
    assert doc_num == 175


def test_param_source_stats():
    cwd = os.path.dirname(__file__)
    test_track = StaticTrack(
        parameters={
            "track-id": "test_file_write",
            "start-date": "2020-01-01:00:00:00",
            "end-date": "2020-01-01:01:00:00",
            "raw-data-volume-per-day": "0.024MB",
            "random-seed": 13,
        },
        generated_document_paths=[
            os.path.join(
                cwd, "resources", "processed_test", "test_corpus_read", "0.json"
            )
        ],
    )

    param_source = ProcessedCorpusParamSource(
        track=test_track,
        params={
            "time-format": "milliseconds",
            "profile": "fixed_interval",
            "bulk-size": 10,
        },
    )
    client_param_source = param_source.partition(partition_index=0, total_partitions=1)
    while True:
        try:
            stats = client_param_source.params()["param-source-stats"]
            assert stats["raw-size-bytes"] == 60
            assert stats["client"] == 0
            assert "event-time-span" in stats
            assert "relative-time" in stats
            assert "index-lag" in stats
            assert "min-timestamp" in stats
            assert "max-timestamp" in stats
        except StopIteration:
            break


def test_missing_bulk_size():
    with pytest.raises(DataError) as data_error:
        ProcessedCorpusParamSource(
            track=StaticTrack(
                parameters={
                    "track-id": "test_file_write",
                    "raw-data-volume-per-day": "0.001MB",
                }
            ),
            params={},
        )
    assert (
        data_error.value.message
        == "Parameter source for operation 'bulk' did not provide the mandatory parameter "
        "'bulk-size'. Add it to your parameter source and try again."
    )


def test_invalid_bulk_size():
    with pytest.raises(InvalidSyntax) as invalid_syntax:
        ProcessedCorpusParamSource(
            track=StaticTrack(
                parameters={
                    "track-id": "test_file_write",
                    "raw-data-volume-per-day": "0.001MB",
                }
            ),
            params={"bulk-size": "aa"},
        )
    assert invalid_syntax.value.message == '"bulk-size" must be numeric'


def test_negative_bulk_size():
    with pytest.raises(InvalidSyntax) as invalid_syntax:
        ProcessedCorpusParamSource(
            track=StaticTrack(
                parameters={
                    "track-id": "test_file_write",
                    "file-cache-dir": "./tmp",
                    "raw-data-volume-per-day": "0.001MB",
                }
            ),
            params={"bulk-size": -1},
        )
    assert invalid_syntax.value.message == '"bulk-size" must be positive but was -1'


def test_no_data_volume():
    with pytest.raises(DataError) as data_error:
        ProcessedCorpusParamSource(
            track=StaticTrack(
                parameters={"bulk-size": 10, "track-id": "test_file_write"}
            ),
            params={},
        )
    assert (
        data_error.value.message
        == "Parameter source for operation 'bulk' did not provide the mandatory parameter "
        "'raw-data-volume-per-day'. Add it to your parameter source and try again."
    )


def test_invalid_dates():
    with pytest.raises(TimeParsingError):
        ProcessedCorpusParamSource(
            track=StaticTrack(
                parameters={
                    "bulk-size": 10,
                    "track-id": "test_file_write",
                    "file-cache-dir": "./tmp",
                    "raw-data-volume-per-day": "0.001MB",
                    "end-date": "wednesday",
                }
            ),
            params={},
        )
    with pytest.raises(TimeParsingError):
        ProcessedCorpusParamSource(
            track=StaticTrack(
                parameters={
                    "bulk-size": 10,
                    "track-id": "test_file_write",
                    "file-cache-dir": "./tmp",
                    "raw-data-volume-per-day": "0.001MB",
                    "start-date": "wednesday",
                }
            ),
            params={},
        )
    # start greater than end
    with pytest.raises(TrackConfigError):
        ProcessedCorpusParamSource(
            track=StaticTrack(
                parameters={
                    "bulk-size": 10,
                    "track-id": "test_file_write",
                    "file-cache-dir": "./tmp",
                    "raw-data-volume-per-day": "0.001MB",
                    "start-date": "2020-09-01:00:00:00",
                    "end-date": "2020-08-31:00:00:00",
                }
            ),
            params={},
        )


def test_undocumented_params():
    cwd = os.path.dirname(__file__)
    test_track = StaticTrack(
        parameters={
            "track-id": "test_file_write",
            "start-date": "2020-05-01:00:00:00",
            "end-date": "2020-06-01:00:00:00",
            "bulk-start-date": "2020-08-31:00:00:00",
            "bulk-end-date": "2020-09-01:00:00:00",
            "raw-data-volume-per-day": "0.001MB",
            "random-seed": 13,
        },
        generated_document_paths=[
            os.path.join(
                cwd,
                "resources",
                "processed_test",
                "test_timespan_corpus_read",
                "0.json",
            )
        ],
    )

    # start-date and end-date should be ignored
    param_source = ProcessedCorpusParamSource(
        track=test_track,
        params={
            "time-format": "milliseconds",
            "profile": "fixed_interval",
            "init-load": True,
            "bulk-size": 175,
        },
    )
    client_param_source = param_source.partition(partition_index=0, total_partitions=1)
    batches = 0
    num_docs = 0
    # 1048.576 bytes raw to be indexed. 6 bytes per doc, so 1048.576/6 = 175 docs
    # batch size is 175 so 175/25 = 1 batch.
    while True:
        try:
            docs = client_param_source.params()
            size = len(docs["body"]) / 2
            assert size == 175
            num_docs += size
            # close to one day
            assert client_param_source.event_time_span == 85906.285764
            assert (
                json.loads(docs["body"][1])["message"]
                == "2020-08-31T00:01:16.123456Z dummy"
            )
            assert (
                json.loads(docs["body"][-1])["message"]
                == "2020-08-31T23:53:03.123456Z dummy"
            )
            batches += 1
        except StopIteration:
            break
    assert batches == 1
    assert num_docs == 175


def test_timestamp_corpus_read_from_multiple_integrations():
    def next_bulk():
        _docs = client_param_source.params()
        _idx_name = json.loads(_docs["body"][0])["create"]["_index"]
        _doc = json.loads(_docs["body"][1])
        return _idx_name, _doc["message"], _doc["@timestamp"]

    cwd = os.path.dirname(__file__)
    test_track = StaticTrack(
        parameters={
            "track-id": "test_file_write",
            "end-date": "2020-09-01:00:00:00",
            "start-date": "2020-08-31:00:00:00",
            # These have changed compared to create_test_track()
            "raw-data-volume-per-day": "0.0001MB",
            "random-seed": 13,
        },
        generated_document_paths=[
            os.path.join(
                cwd,
                "resources",
                "processed_test",
                "test_corpus_read_multiple_integrations",
                "0.json",
            )
        ],
    )

    param_source = ProcessedCorpusParamSource(
        track=test_track,
        params={
            "time-format": "milliseconds",
            "profile": "fixed_interval",
            "bulk-size": 1,
        },
    )
    client_param_source = param_source.partition(partition_index=0, total_partitions=1)

    # see test_timestamp_corpus_read() for expected timestamps for the defined timerange and corpus size
    timestamps = {
        "apache-access-logs": "31/Aug/2020:00:12:26 +0000",
        "apache-error-logs": "Mon Aug 31 01:32:26 2020",
        "application-logs-1": "2020-08-31T02:52:26.435Z",
        "application-logs-2": "2020-08-31T04:12:26.435Z",
        "kafka-logs": "2020-08-31 05:32:26",
        "mysql-error-logs": "2020-08-31 06:52:26",
        "mysql-slowlog-logs": "1598875946",
        "nginx-access-logs": "31/Aug/2020:09:32:26 +0000",
        "nginx-access-logs-2": "31/Aug/2020:10:52:26 +0000",
        "nginx-error-logs": "2020/08/31 12:12:26",
        "nginx-error-logs-2": "2020/08/31 13:32:26",
        "postgresql-logs": "2020-08-31 14:52:26",
        "redis-app-logs": "31 Aug 16:12:26",
        "redis-app-slowlogs": "2020-08-31T17:32:26.435Z",
        "system-auth-logs": "2020-08-31T18:52:26.775113Z",
        "system-auth-logs-2": "2020-08-31T20:12:26.775113Z",
        "system-syslog-logs": "2020-08-31T21:32:26.775113Z",
        "system-syslog-logs-2": "2020-08-31T22:52:26.775113Z",
    }

    idx_name, doc_message, _ = next_bulk()
    expected_idx_name = "apache-access-logs"
    assert idx_name == expected_idx_name
    assert (
        doc_message
        == f'10.12.9.197 - brownantonio [{timestamps[expected_idx_name]}] "GET / HTTP/1.1" 200 1203 "-" "Elastic-Heartbeat/7.8.0 (linux; amd64; f79387d32717d79f689d94fda1ec80b2cf285d30; 2020-06-14 17:31:16 +0000 UTC)"'
    )

    idx_name, doc_message, _ = next_bulk()
    expected_idx_name = "apache-error-logs"
    assert idx_name == expected_idx_name
    assert (
        doc_message
        == f"[{timestamps[expected_idx_name]}] [core:info] [pid 994682:tid 677381] [client 10.12.9.220:35782] AH00128: File does not exist: /var/www/html/wp-login.ph, referer: shopify.com"
    )

    idx_name, doc_message, ts = next_bulk()
    expected_idx_name = "application-logs-1"  # aka k8s-stats
    assert idx_name == expected_idx_name
    assert (
        doc_message
        == '82.36.71.189 - [82.36.71.189] - elasticsearch-ci [07/Sep/2020:10:28:35 +0000] "GET /cache/c2d427d5ecd9155176c39090541beb49 HTTP/1.1" 200 2412 "-" "Gradle/6.6.1 (Linux;4.12.14-lp151.28.63-default;amd64) (Oracle Corporation;14.0.2;14.0.2+12-46)" 409 0.008 [elasticsearch-gradle-proxy-80] 82.36.71.189:9080 2412 0.008 200'
    )
    assert ts == timestamps[expected_idx_name]

    idx_name, doc_message, ts = next_bulk()
    expected_idx_name = "application-logs-2"  # aka eden-stats
    assert idx_name == expected_idx_name
    assert (
        doc_message == "\u001b[0mGET / \u001b[32m200 \u001b[0m0.592 ms - 2410\u001b[0m"
    )
    assert ts == timestamps[expected_idx_name]

    idx_name, doc_message, _ = next_bulk()
    expected_idx_name = "kafka-logs"
    assert idx_name == expected_idx_name
    assert (
        doc_message
        == timestamps[expected_idx_name]
        + ",544. DEBUG [ReplicaFetcher replicaId=2, leaderId=1, fetcherId=0]: Built incremental fetch (sessionId=998038420, epoch=3028672) for node 1. Added 0 partition(s), altered 0 partition(s), removed 0 partition(s) out of 24 partition(s) (org.apache.kafka.clients.FetchSessionHandler)"
    )

    idx_name, doc_message, _ = next_bulk()
    expected_idx_name = "mysql-error-logs"
    assert idx_name == expected_idx_name
    assert (
        doc_message
        == timestamps[expected_idx_name]
        + " 3328971 [Note] Access denied for user 'root'@'10.12.6.38' (using password: YES)"
    )

    idx_name, doc_message, _ = next_bulk()
    expected_idx_name = "mysql-slowlog-logs"
    assert idx_name == expected_idx_name
    assert (
        doc_message
        == "# User@Host: stevenssandra[root] @  [10.12.7.63]  Id: 4756535\n# Query_time: 0.00061  Lock_time: 0.000057 Rows_sent: 99 Rows_examined: 99   \nSET timestamp="
        + timestamps[expected_idx_name]
        + ";\nSELECT intcol1,intcol2,intcol3,intcol4,intcol5,intcol6,intcol7,charcol1,charcol2,charcol3,charcol4,charcol5,charcol6,charcol7 FROM t1\u0000;"
    )

    idx_name, doc_message, _ = next_bulk()
    expected_idx_name = "nginx-access-logs"  # demo.elastic.co
    assert idx_name == expected_idx_name
    assert (
        doc_message
        == "134.68.249.190 - danielle15 ["
        + timestamps[expected_idx_name]
        + '] "GET / HTTP/1.1" 200 649 "" "Elastic-Heartbeat/7.8.0 (linux; amd64; f79387d32717d79f689d94fda1ec80b2cf285d30; 2020-06-14 17:31:16 +0000 UTC)"'
    )

    idx_name, doc_message, _ = next_bulk()
    expected_idx_name = "nginx-access-logs-2"  # infra-stats
    assert idx_name == expected_idx_name
    assert (
        doc_message
        == "93.191.78.166 - wendy13 ["
        + timestamps[expected_idx_name]
        + '] "GET /whoAmI/ HTTP/1.1" 200 6927 "-" "GoogleHC/1.0"'
    )

    idx_name, doc_message, _ = next_bulk()
    expected_idx_name = "nginx-error-logs"  # demo.elastic.co
    assert idx_name == expected_idx_name
    assert (
        doc_message
        == timestamps[expected_idx_name]
        + ' [info] 18#18: *6831822 [lua] ip_blacklist.lua:15: Loading REDIS Cache, client: 106.172.245.114, server: green.demo.elastic.co, request: "GET /status HTTP/1.1", host: "demo.elastic.co"'
    )

    idx_name, doc_message, _ = next_bulk()
    expected_idx_name = "nginx-error-logs-2"  # infra-stats
    assert idx_name == expected_idx_name
    assert (
        doc_message
        == timestamps[expected_idx_name]
        + ' [error] 26284#26284: *244030 limiting requests, dry run, excess: 50.256 by zone "jenkins_global", client: 211.174.195.82, server: kibana-ci.elastic.co, request: "GET /static/4ffe5b59/descriptor/hudson.plugins.gradle.GradleOutcomeNote/style.css HTTP/1.1", host: "kibana-ci.elastic.co"'
    )

    idx_name, doc_message, _ = next_bulk()
    expected_idx_name = "postgresql-logs"
    assert idx_name == expected_idx_name
    assert (
        doc_message
        == timestamps[expected_idx_name]
        + '.870 UTC [3894076] elastic@opbeans LOG:  duration: 0.236 ms  statement <unnamed>: SELECT "opbeans_orderline"."id", "opbeans_orderline"."order_id", "opbeans_orderline"."product_id", "opbeans_orderline"."amount", "opbeans_product"."id", "opbeans_product"."sku", "opbeans_product"."name", "opbeans_product"."description", "opbeans_product"."product_type_id", "opbeans_product"."stock", "opbeans_product"."cost", "opbeans_product"."selling_price" FROM "opbeans_orderline" INNER JOIN "opbeans_product" ON ("opbeans_orderline"."product_id" = "opbeans_product"."id") WHERE "opbeans_orderline"."order_id" = 74649'
    )

    idx_name, doc_message, _ = next_bulk()
    expected_idx_name = "redis-app-logs"
    assert idx_name == expected_idx_name
    assert (
        doc_message
        == f"1:M {timestamps[expected_idx_name]}.464 - Accepted 10.12.9.203:40122"
    )

    idx_name, doc_message, ts = next_bulk()
    expected_idx_name = "redis-app-slowlogs"
    assert idx_name == expected_idx_name
    assert (
        doc_message == "ZREVRANGEBYSCORE ip_blacklist 9223372036854775807 -1 WITHSCORES"
    )
    assert ts == timestamps[expected_idx_name]

    idx_name, doc_message, _ = next_bulk()
    expected_idx_name = "system-auth-logs"  # infra-stats
    assert idx_name == expected_idx_name
    assert (
        doc_message
        == timestamps[expected_idx_name]
        + " packer-5f3c21c5-cff2-f924-ed7a-0beb9d7363cc sudo: pam_unix(sudo:session): session closed for user root"
    )

    idx_name, doc_message, _ = next_bulk()
    expected_idx_name = "system-auth-logs-2"  # demo.elastic.co
    assert idx_name == expected_idx_name
    assert (
        doc_message
        == timestamps[expected_idx_name]
        + " server-02 sshd[8252]: Received disconnect from 175.158.50.75 port 31759:11: Bye Bye [preauth]"
    )

    idx_name, doc_message, _ = next_bulk()
    expected_idx_name = "system-syslog-logs"  # infra-stats
    assert idx_name == expected_idx_name
    assert (
        doc_message
        == timestamps[expected_idx_name]
        + " packer-5f3c21c5-cff2-f924-ed7a-0beb9d7363cc systemd[1]: Stopped Execute cloud user/final scripts."
    )

    idx_name, doc_message, _ = next_bulk()
    expected_idx_name = "system-syslog-logs-2"  # demo.elastic.co
    assert idx_name == expected_idx_name
    assert (
        doc_message
        == timestamps[expected_idx_name]
        + " workstation-03 systemd: Started Docker Cleanup."
    )

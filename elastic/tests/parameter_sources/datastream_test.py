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
import os

# Import from logs track.py where SequentialDataStreamParamSource and DLMBulkIndexParamSource are defined
import sys

from shared.parameter_sources.datastream import (
    CreateDataStreamParamSource,
    DataStreamParamSource,
    DLMBulkIndexParamSource,
    SequentialDataStreamParamSource,
)
from tests.parameter_sources import StaticTrack


def test_read_track_data_streams():
    data_stream_source = DataStreamParamSource(StaticTrack(), params={})
    data_streams = [
        "logs-system.syslog-default",
        "logs-elastic.agent-default",
        "logs-elastic.kafka-default",
    ]
    i = 0
    while True:
        try:
            params = data_stream_source.params()
            assert params["data-stream"] == data_streams[i]
            i += 1
            pass
        except StopIteration:
            break
    assert i == 3


def test_read_data_stream():
    data_stream_source = DataStreamParamSource(StaticTrack(), params={"data-stream": "logs-elastic.agent-default"})
    params = data_stream_source.params()
    assert params["data-stream"] == "logs-elastic.agent-default"


def test_read_data_stream_list():
    data_streams = ["test-1", "test-2"]
    data_stream_source = DataStreamParamSource(StaticTrack(), params={"data-stream": data_streams})
    i = 0
    while True:
        try:
            params = data_stream_source.params()
            assert params["data-stream"] == data_streams[i]
            i += 1
            pass
        except StopIteration:
            break
    assert i == 2


def test_create_data_stream_list():
    indices = ["logs-system.test", "logs-kafka.test", "logs-system.test"]
    create_data_stream_source = CreateDataStreamParamSource(
        StaticTrack(
            parameters={
                "integration-ratios": {
                    "agent": {"corpora": {"agent-logs": 0.5}},
                    "kafka": {"corpora": {"kafka-logs": 0.25}},
                    "system": {"corpora": {"system-logs": 0.25}},
                }
            }
        ),
        params={},
    )
    i = 0
    while True:
        try:
            params = create_data_stream_source.params()
            assert params["data-stream"] == indices[i]
            i += 1
            pass
        except StopIteration:
            break
    # duplicates should be removed
    assert i == 2


def test_create_no_data_streams():
    create_data_stream_source = CreateDataStreamParamSource(StaticTrack(parameters={"integration-ratios": {}}), params={})
    i = 0
    while True:
        try:
            create_data_stream_source.params()
            i += 1
            pass
        except StopIteration:
            break
    assert i == 0


def test_sequential_datastream_basic():
    """Test basic sequential data stream name generation."""
    source = SequentialDataStreamParamSource(StaticTrack(), params={"data-stream-prefix": "test-ds", "start-index": 0})

    # Generate 5 data stream names
    expected_names = ["test-ds-0", "test-ds-1", "test-ds-2", "test-ds-3", "test-ds-4"]
    for i in range(5):
        params = source.params()
        assert params["data-stream"] == expected_names[i]
        assert params["ignore-existing"] is False


def test_sequential_datastream_custom_start_index():
    """Test sequential data stream generation with custom start index."""
    source = SequentialDataStreamParamSource(StaticTrack(), params={"data-stream-prefix": "dlm-benchmark", "start-index": 100})

    params = source.params()
    assert params["data-stream"] == "dlm-benchmark-100"
    params = source.params()
    assert params["data-stream"] == "dlm-benchmark-101"


def test_sequential_datastream_ignore_existing():
    """Test that ignore-existing parameter is passed through."""
    source = SequentialDataStreamParamSource(
        StaticTrack(), params={"data-stream-prefix": "test", "start-index": 0, "ignore-existing": True}
    )

    params = source.params()
    assert params["ignore-existing"] is True


def test_sequential_datastream_partition():
    """Test partitioning across multiple clients."""
    source = SequentialDataStreamParamSource(StaticTrack(), params={"data-stream-prefix": "test-ds", "start-index": 0})

    # Partition into 3 clients
    partition_0 = source.partition(0, 3)
    partition_1 = source.partition(1, 3)
    partition_2 = source.partition(2, 3)

    # Each partition should generate non-overlapping names
    # Client 0: 0, 3, 6, 9...
    assert partition_0.params()["data-stream"] == "test-ds-0"
    assert partition_0.params()["data-stream"] == "test-ds-3"
    assert partition_0.params()["data-stream"] == "test-ds-6"

    # Client 1: 1, 4, 7, 10...
    assert partition_1.params()["data-stream"] == "test-ds-1"
    assert partition_1.params()["data-stream"] == "test-ds-4"
    assert partition_1.params()["data-stream"] == "test-ds-7"

    # Client 2: 2, 5, 8, 11...
    assert partition_2.params()["data-stream"] == "test-ds-2"
    assert partition_2.params()["data-stream"] == "test-ds-5"
    assert partition_2.params()["data-stream"] == "test-ds-8"


def test_dlm_bulk_basic():
    """Test basic DLM bulk parameter generation."""
    source = DLMBulkIndexParamSource(StaticTrack(), params={"data-stream-prefix": "dlm-test", "data-stream-count": 5, "bulk-size": 10})

    params = source.params()

    # Check returned parameters
    assert "body" in params
    assert params["action-metadata-present"] is True
    assert params["bulk-size"] == 10
    assert params["unit"] == "docs"

    # Check body format - should have 20 lines (10 docs * 2 lines each)
    lines = params["body"].strip().split("\n")
    assert len(lines) == 20

    # Check that first line is metadata with _index
    import json

    first_line = json.loads(lines[0])
    assert "create" in first_line
    assert "_index" in first_line["create"]
    assert first_line["create"]["_index"].startswith("dlm-test-")

    # Check that second line is a document
    second_line = json.loads(lines[1])
    assert "@timestamp" in second_line
    assert "message" in second_line
    assert "host" in second_line
    assert "service" in second_line
    assert "log" in second_line


def test_dlm_bulk_round_robin():
    """Test that DLM bulk indexes round-robin through data streams."""
    source = DLMBulkIndexParamSource(StaticTrack(), params={"data-stream-prefix": "dlm-test", "data-stream-count": 3, "bulk-size": 1})

    import json

    # First bulk should go to dlm-test-0
    params1 = source.params()
    lines1 = params1["body"].strip().split("\n")
    meta1 = json.loads(lines1[0])
    assert meta1["create"]["_index"] == "dlm-test-0"

    # Second bulk should go to dlm-test-1
    params2 = source.params()
    lines2 = params2["body"].strip().split("\n")
    meta2 = json.loads(lines2[0])
    assert meta2["create"]["_index"] == "dlm-test-1"

    # Third bulk should go to dlm-test-2
    params3 = source.params()
    lines3 = params3["body"].strip().split("\n")
    meta3 = json.loads(lines3[0])
    assert meta3["create"]["_index"] == "dlm-test-2"

    # Fourth bulk should wrap around to dlm-test-0
    params4 = source.params()
    lines4 = params4["body"].strip().split("\n")
    meta4 = json.loads(lines4[0])
    assert meta4["create"]["_index"] == "dlm-test-0"


def test_dlm_bulk_partition():
    """Test DLM bulk partitioning across multiple clients."""
    source = DLMBulkIndexParamSource(StaticTrack(), params={"data-stream-prefix": "dlm-test", "data-stream-count": 10, "bulk-size": 1})

    import json

    # Partition into 3 clients
    partition_0 = source.partition(0, 3)
    partition_1 = source.partition(1, 3)
    partition_2 = source.partition(2, 3)

    # Client 0 should start at index 0 and step by 3
    params_0_1 = partition_0.params()
    lines_0_1 = params_0_1["body"].strip().split("\n")
    meta_0_1 = json.loads(lines_0_1[0])
    assert meta_0_1["create"]["_index"] == "dlm-test-0"

    params_0_2 = partition_0.params()
    lines_0_2 = params_0_2["body"].strip().split("\n")
    meta_0_2 = json.loads(lines_0_2[0])
    assert meta_0_2["create"]["_index"] == "dlm-test-3"

    # Client 1 should start at index 1 and step by 3
    params_1_1 = partition_1.params()
    lines_1_1 = params_1_1["body"].strip().split("\n")
    meta_1_1 = json.loads(lines_1_1[0])
    assert meta_1_1["create"]["_index"] == "dlm-test-1"

    params_1_2 = partition_1.params()
    lines_1_2 = params_1_2["body"].strip().split("\n")
    meta_1_2 = json.loads(lines_1_2[0])
    assert meta_1_2["create"]["_index"] == "dlm-test-4"

    # Client 2 should start at index 2 and step by 3
    params_2_1 = partition_2.params()
    lines_2_1 = params_2_1["body"].strip().split("\n")
    meta_2_1 = json.loads(lines_2_1[0])
    assert meta_2_1["create"]["_index"] == "dlm-test-2"


def test_dlm_bulk_document_structure():
    """Test that generated documents have the correct structure."""
    source = DLMBulkIndexParamSource(StaticTrack(), params={"data-stream-prefix": "dlm-test", "data-stream-count": 1, "bulk-size": 5})

    import json

    params = source.params()
    lines = params["body"].strip().split("\n")

    # Check all documents have required fields
    for i in range(0, len(lines), 2):
        doc = json.loads(lines[i + 1])
        assert "@timestamp" in doc
        assert "message" in doc
        assert "host" in doc
        assert "hostname" in doc["host"]
        assert "service" in doc
        assert "name" in doc["service"]
        assert doc["service"]["name"] == "dlm-benchmark"
        assert "log" in doc
        assert "level" in doc["log"]
        assert doc["log"]["level"] == "info"


def test_dlm_bulk_infinite():
    """Test that DLM bulk source is marked as infinite."""
    source = DLMBulkIndexParamSource(StaticTrack(), params={"data-stream-prefix": "dlm-test", "data-stream-count": 1, "bulk-size": 1})

    assert source.infinite is True

    # Should be able to generate many bulks without stopping
    for _ in range(100):
        params = source.params()
        assert params is not None

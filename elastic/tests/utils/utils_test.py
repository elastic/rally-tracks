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

from esrally.track import Track, DocumentCorpus, Documents
from tests.parameter_sources import StaticTrack
from shared.utils.corpus import (
    calculate_corpus_counts,
    calculate_integration_ratios,
    bounds,
    convert_to_gib,
)
from shared.utils.track import generate_track_id


def test_generate_track_id():
    corpus = DocumentCorpus(
        name="system-logs",
        documents=[
            Documents(
                "bulk",
                document_file="./data/logs-system.syslog-default.json",
                number_of_documents=19637,
                uncompressed_size_in_bytes=26128253,
                target_index="logs-system.syslog-default",
            )
        ],
    )
    track = Track("test_track", corpora=[corpus])
    assert generate_track_id(track) == generate_track_id(track)


def test_corpus_count_calculation():
    counts = calculate_corpus_counts(
        {
            "system-logs": {
                "avg_doc_size": 1024,
                "raw_json_ratio": 10.0,
                "avg_doc_size_with_meta": 1024,
                "avg_message_size": 1024 / 10.0,
            },
            "agent-logs": {
                "avg_doc_size": 1024,
                "raw_json_ratio": 20.0,
                "avg_doc_size_with_meta": 1024,
                "avg_message_size": 1024 / 20.0,
            },
        },
        {"system-logs": 0.5, "agent-logs": 0.5},
        10,
        max_generation_size_gb=10,
    )
    assert counts["system-logs"] == 3495254
    assert counts["agent-logs"] == 6990507


def test_corpus_count_calculation_unlimited():
    counts = calculate_corpus_counts(
        {
            "system-logs": {
                "avg_doc_size": 1024,
                "raw_json_ratio": 10.0,
                "avg_doc_size_with_meta": 1024,
                "avg_message_size": 1024 / 10.0,
            },
            "agent-logs": {
                "avg_doc_size": 1024,
                "raw_json_ratio": 20.0,
                "avg_doc_size_with_meta": 1024,
                "avg_message_size": 1024 / 20.0,
            },
        },
        {"system-logs": 0.5, "agent-logs": 0.5},
        10,
    )
    assert counts["system-logs"] == 52428800
    assert counts["agent-logs"] == 104857600


def test_corpus_ratio_calculation():
    ratios = calculate_integration_ratios({"system-logs": 75, "agent-logs": 25})
    assert ratios["system-logs"] == 0.75
    assert ratios["agent-logs"] == 0.25


def test_bounds_calculation():
    offset, docs = bounds(10, 0, 2)
    assert offset == 0
    assert docs == 5
    offset, docs = bounds(10, 1, 2)
    assert offset == 5
    assert docs == 5
    offset, docs = bounds(10, 0, 3)
    assert offset == 0
    assert docs == 3
    offset, docs = bounds(10, 1, 3)
    assert offset == 3
    assert docs == 3
    offset, docs = bounds(10, 2, 3)
    assert offset == 6
    assert docs == 4


def test_even_bounds_calculation():
    offset, docs = bounds(10, 0, 3)
    assert offset == 0
    assert docs == 3
    offset, docs = bounds(100, 0, 3, ensure_even=True)
    assert offset == 0
    assert docs == 34
    offset, docs = bounds(100, 1, 3, ensure_even=True)
    assert offset == 34
    assert docs == 34
    offset, docs = bounds(100, 2, 3, ensure_even=True)
    assert offset == 68
    assert docs == 32


def test_bounds_more_clients_than_docs():
    offset, docs = bounds(2, 0, 5)
    assert offset == 0
    assert docs == 1
    offset, docs = bounds(2, 1, 5)
    assert offset == 1
    assert docs == 1
    offset, docs = bounds(2, 2, 5)
    assert docs == 0
    offset, docs = bounds(2, 3, 5)
    assert docs == 0
    offset, docs = bounds(2, 4, 5)
    assert docs == 0


def test_convert_to_gib():
    assert convert_to_gib("1GB") == 1.0
    assert convert_to_gib("2G") == 2.0
    assert convert_to_gib("1MB") == 0.0009765625
    assert convert_to_gib("1024M") == 1.0
    assert convert_to_gib("1TB") == 1024
    assert convert_to_gib("2T") == 2048
    assert convert_to_gib("1PB") == 1048576
    assert convert_to_gib("2P") == 2097152

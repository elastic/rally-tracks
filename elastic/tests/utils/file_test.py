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
from esrally.utils import io

from shared.utils.file import FileMetadata, WrappingSlice, JsonFileReader, CorpusReader

cwd = os.path.dirname(__file__)


def test_meta_read():
    number_docs, message_size = FileMetadata.read(os.path.join(cwd, "resources", "0"))
    assert number_docs == 1000
    assert message_size == 10000


def test_meta_write(tmp_path):
    FileMetadata.write(
        output_folder=tmp_path, client_index="0", number_docs=100, message_size=1000
    )
    number_docs, message_size = FileMetadata.read(os.path.join(tmp_path, "0"))
    assert number_docs == 100
    assert message_size == 1000


def json_test_processor(doc_bytes, _, __):
    return json.loads(doc_bytes.decode("utf-8")), 0


def _get_corpus_reader():
    readers = [
        JsonFileReader(
            os.path.join(cwd, "resources", "sample-1.json"),
            WrappingSlice(io.MmapSource, 0, 2),
            json_test_processor,
            "test-index",
            "test-corpus",
        ),
        JsonFileReader(
            os.path.join(cwd, "resources", "sample-2.json"),
            WrappingSlice(io.MmapSource, 0, 2),
            json_test_processor,
            "test-index",
            "test-corpus",
        ),
    ]
    return CorpusReader(readers, 1)


def test_corpus_reader():
    corpus_reader = _get_corpus_reader()
    corpus_reader.open()
    for i in range(0, 10):
        num_docs, docs, size = next(corpus_reader)
        assert len(docs) == 2
        doc = docs[1]
        assert (i % 4) + 1 == doc["id"]
    corpus_reader.close()


def test_corpus_reader_with_context_manager():
    corpus_reader = _get_corpus_reader()
    with corpus_reader:
        for i in range(0, 10):
            num_docs, docs, size = next(corpus_reader)
            assert len(docs) == 2
            doc = docs[1]
            assert (i % 4) + 1 == doc["id"]


def test_invalid_read():
    readers = [
        JsonFileReader(
            os.path.join(cwd, "resources", "sample-does-not-exist.json"),
            WrappingSlice(io.MmapSource, 0, 2),
            json_test_processor,
            "test-index",
            "test-corpus",
        )
    ]
    corpus_reader = CorpusReader(readers, 1)
    with pytest.raises(FileNotFoundError):
        with corpus_reader:
            pass
    with pytest.raises(FileNotFoundError):
        corpus_reader.open()


def test_set_bulk_size():
    readers = [
        JsonFileReader(
            os.path.join(cwd, "resources", "sample-3.json"),
            WrappingSlice(io.MmapSource, 0, 10),
            json_test_processor,
            "test-index",
            "test-corpus",
        )
    ]
    corpus_reader = CorpusReader(readers, 1)
    with corpus_reader:
        for i in range(0, 4):
            num_docs, docs, size = next(corpus_reader)
            assert len(docs) == 2
            doc = docs[1]
            assert i == doc["id"]
            print(i)
        corpus_reader.set_bulk_size(2)
        for i in range(4, 9, 2):
            print(i)
            num_docs, docs, size = next(corpus_reader)
            assert len(docs) == 4
            assert i == docs[1]["id"]
            assert i + 1 == docs[3]["id"]

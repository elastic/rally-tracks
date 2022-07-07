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
import datetime
import json
import os
import random

import pytest
from esrally.exceptions import TrackConfigError, RallyAssertionError, DataError

from shared.track_processors.data_generator import DataGenerator, CorpusGenerator
from shared.parameter_sources.processed import ProcessedCorpusParamSource, MagicNumbers
from shared.utils.time import TimeParsingError
from tests.parameter_sources import StaticTrack


def read_file(path):
    with open(path, "rt") as f:
        return f.readlines()


def docs(lines):
    # iterate over every other line starting from line 1.
    for line in lines[1::2]:
        doc = json.loads(line)
        yield doc


def generate(track, data_root_path):
    generator = DataGenerator()
    generator.on_after_load_track(track)
    cached = True
    for task, params in generator.on_prepare_track(track, data_root_dir=data_root_path):
        cached = task(**params)
    # set absolute data path - this is done by Rally
    set_absolute_data_path(track, data_root_path)
    return cached


def set_absolute_data_path(track, data_root_path):
    generated_corpus = find_generated_corpus(track)
    if generated_corpus:
        for doc_set in generated_corpus.documents:
            doc_set.document_file = os.path.join(
                data_root_path, track.name, doc_set.document_file
            )


def assert_rally_properties(lines):
    for doc in docs(lines):
        assert (
            "rally" in doc
            and "doc_size" in doc["rally"]
            and "message_size" in doc["rally"]
        )


def find_generated_corpus(track):
    return next((c for c in track.corpora if c.meta_data.get("generated", False)), None)


def test_processed_file_read(tmp_path):
    track_id = "test_processed_file_read"
    test_track = StaticTrack(
        parameters={
            "raw-data-volume-per-day": "0.1MB",
            "max-generated-corpus-size": "0.1MB",
            "track-id": track_id,
            "integration-ratios": {
                "system": {"corpora": {"system-logs": 0.5}},
                "agent": {"corpora": {"agent-logs": 0.5}},
            },
            "sample-size": 10,
            "generator-batch-size": 10000,
            "data-generation-clients": 1,
        }
    )

    generate(test_track, tmp_path)
    generated_corpus = find_generated_corpus(test_track)
    lines_in_data_file = read_file(generated_corpus.documents[0].document_file)

    assert len(lines_in_data_file) == 156
    assert generated_corpus.documents[0].number_of_documents == 78
    assert_rally_properties(lines_in_data_file)
    assert test_track.selected_challenge_or_default.parameters[
        "output-folder"
    ] == os.path.join(tmp_path, test_track.name, "generated", track_id)
    assert os.path.exists(f"{generated_corpus.documents[0].document_file}.offset")


def test_offset_generation(tmp_path):
    track_id = "test_offset_generation"
    test_track = StaticTrack(
        parameters={
            "raw-data-volume-per-day": "0.1MB",
            "max-generated-corpus-size": "0.1MB",
            "track-id": track_id,
            "integration-ratios": {
                "system": {"corpora": {"system-logs": 0.5}},
                "agent": {"corpora": {"agent-logs": 0.5}},
            },
            "sample-size": 10,
            "generator-batch-size": 1,
            "data-generation-clients": 1,
            "offset-increment": 10,
        }
    )
    generate(test_track, tmp_path)
    generated_corpus = find_generated_corpus(test_track)
    lines_in_data_file = read_file(generated_corpus.documents[0].document_file)

    assert len(lines_in_data_file) == 156
    offset_file = f"{generated_corpus.documents[0].document_file}.offset"
    assert os.path.exists(offset_file)
    lines_in_offset = read_file(offset_file)
    assert len(lines_in_offset) == 15
    for offset in lines_in_offset:
        assert int(offset.split(";")[0]) % 10 == 0


def test_invalid_offset_generation(tmp_path):
    track_id = "test_offset_generation"
    with pytest.raises(RallyAssertionError) as assertion_error:
        test_track = StaticTrack(
            parameters={
                "raw-data-volume-per-day": "0.1MB",
                "max-generated-corpus-size": "0.1MB",
                "track-id": track_id,
                "integration-ratios": {
                    "system": {"corpora": {"system-logs": 0.5}},
                    "agent": {"corpora": {"agent-logs": 0.5}},
                },
                "sample-size": 10,
                "generator-batch-size": 100,
                "data-generation-clients": 1,
                "offset-increment": 10,
            }
        )
        generate(test_track, tmp_path)
    assert (
        assertion_error.value.message
        == "generator-batch-size [100] cannot be greater than offset-increment [10]"
    )


def test_processed_file_read_with_no_limit(tmp_path):
    # here we will get more than 0.1MB due to JSON expansion and no limit
    track_id = "test_processed_file_read_with_no_limit"
    test_track = StaticTrack(
        parameters={
            "raw-data-volume-per-day": "0.1MB",
            "max-generated-corpus-size": "10GB",
            "track-id": track_id,
            "integration-ratios": {
                "system": {"corpora": {"system-logs": 0.5}},
                "agent": {"corpora": {"agent-logs": 0.5}},
            },
            "sample-size": 10,
            "generator-batch-size": 10000,
            "data-generation-clients": 1,
        }
    )

    generate(test_track, tmp_path)

    generated_corpus = find_generated_corpus(test_track)
    lines_in_data_file = read_file(generated_corpus.documents[0].document_file)

    assert len(lines_in_data_file) == 2776
    assert generated_corpus.documents[0].number_of_documents == 1388
    assert_rally_properties(lines_in_data_file)


def test_doc_size_calc(tmp_path):
    track_id = "test_doc_size_calc"
    test_track = StaticTrack(
        parameters={
            "raw-data-volume-per-day": "0.1MB",
            "max-generated-corpus-size": "0.1MB",
            "track-id": track_id,
            "integration-ratios": {"kafka": {"corpora": {"kafka-logs": 1.0}}},
            "exclude-properties": {"kafka-logs": ["host"]},
            "generator-batch-size": 10000,
            "data-generation-clients": 1,
        }
    )

    generate(test_track, tmp_path)
    generated_corpus = find_generated_corpus(test_track)
    lines_in_data_file = read_file(generated_corpus.documents[0].document_file)

    for doc in docs(lines_in_data_file):
        assert doc["rally"]["doc_size"] == 1680
        assert doc["rally"]["message_size"] == 117


def test_multiple_clients_read(tmp_path):
    track_id = "test_multiple_clients_read"
    test_track = StaticTrack(
        parameters={
            "raw-data-volume-per-day": "0.1MB",
            "max-generated-corpus-size": "0.1MB",
            "random-seed": 13,
            "track-id": track_id,
            "integration-ratios": {
                "system": {"corpora": {"system-logs": 0.5}},
                "agent": {"corpora": {"agent-logs": 0.5}},
            },
            "sample-size": 10,
            "generator-batch-size": 10000,
            "data-generation-clients": 2,
        }
    )

    generate(test_track, tmp_path)
    generated_corpus = find_generated_corpus(test_track)
    # 2 clients generated two data files
    assert len(generated_corpus.documents) == 2

    lines_in_data_file_client_0 = read_file(generated_corpus.documents[0].document_file)
    lines_in_data_file_client_1 = read_file(generated_corpus.documents[1].document_file)

    assert len(lines_in_data_file_client_0) == 76
    assert len(lines_in_data_file_client_1) == 82


def test_cache_usage(tmp_path):
    params = {
        "raw-data-volume-per-day": "0.1MB",
        "max-generated-corpus-size": "0.1MB",
        "track-id": "test_cache_usage",
        "integration-ratios": {
            "system": {"corpora": {"system-logs": 0.5}},
            "agent": {"corpora": {"agent-logs": 0.5}},
        },
        "sample-size": 10,
        "generator-batch-size": 10000,
        "data-generation-clients": 1,
    }

    test_track_1 = StaticTrack(parameters=params)
    test_track_2 = StaticTrack(parameters=params)

    cached = generate(test_track_1, tmp_path)
    assert not cached

    cached = generate(test_track_2, tmp_path)
    assert cached

    lines_in_data_track_1 = read_file(
        find_generated_corpus(test_track_1).documents[0].document_file
    )
    lines_in_data_track_2 = read_file(
        find_generated_corpus(test_track_2).documents[0].document_file
    )
    assert lines_in_data_track_1 == lines_in_data_track_2


def test_cache_override(tmp_path):
    params = {
        "raw-data-volume-per-day": "0.1MB",
        "max-generated-corpus-size": "0.1MB",
        "track-id": "test_cache_override",
        "force-data-generation": True,
        "integration-ratios": {
            "system": {"corpora": {"system-logs": 0.5}},
            "agent": {"corpora": {"agent-logs": 0.5}},
        },
        "sample-size": 10,
        "generator-batch-size": 10000,
        "data-generation-clients": 1,
    }

    test_track_1 = StaticTrack(parameters=params)
    test_track_2 = StaticTrack(parameters=params)

    cached = generate(test_track_1, tmp_path)
    assert not cached

    cached = generate(test_track_2, tmp_path)
    # we forced regenerating data
    assert not cached

    lines_in_data_track_1 = read_file(
        find_generated_corpus(test_track_1).documents[0].document_file
    )
    lines_in_data_track_2 = read_file(
        find_generated_corpus(test_track_2).documents[0].document_file
    )
    assert lines_in_data_track_1 == lines_in_data_track_2


def test_exclude_property(tmp_path):
    track_id = "test_exclude_property"
    test_track = StaticTrack(
        parameters={
            "raw-data-volume-per-day": "0.1MB",
            "max-generated-corpus-size": "0.1MB",
            "track-id": track_id,
            "integration-ratios": {"system": {"corpora": {"system-logs": 1.0}}},
            "exclude-properties": {"system-logs": ["host"]},
            "sample-size": 10,
            "generator-batch-size": 10000,
            "data-generation-clients": 1,
        }
    )

    generate(test_track, tmp_path)

    generated_corpus = find_generated_corpus(test_track)

    lines_in_data_file = read_file(generated_corpus.documents[0].document_file)
    assert len(lines_in_data_file) == 256
    assert generated_corpus.documents[0].number_of_documents == 128
    for doc in docs(lines_in_data_file):
        assert "host" not in doc
    assert_rally_properties(lines_in_data_file)


def test_hr_date_ranges(tmp_path):
    track_id = "test_hr_date_ranges"
    test_track = StaticTrack(
        parameters={
            "integration-ratios": {
                "system": {"corpora": {"system-logs": 0.5}},
                "agent": {"corpora": {"agent-logs": 0.5}},
            },
            "raw-data-volume-per-day": "2.4MB",
            "max-generated-corpus-size": "2.4MB",
            "track-id": track_id,
            # run for 1h which means 0.1mb per hr. The size is based on the raw data volume but capped by the total json
            # capped by the max-generation-size
            "start-date": "now",
            "end-date": "now+1h",
            "sample-size": 10,
            "generator-batch-size": 10000,
            "data-generation-clients": 1,
        }
    )

    generate(test_track, tmp_path)
    generated_corpus = find_generated_corpus(test_track)
    lines_in_data_file = read_file(generated_corpus.documents[0].document_file)

    assert len(lines_in_data_file) == 2776
    assert generated_corpus.documents[0].number_of_documents == 1388
    assert_rally_properties(lines_in_data_file)

    message_size = sum(
        [doc["rally"]["message_size"] for doc in docs(lines_in_data_file)]
    )
    assert round(message_size / 1024 / 1024, 1) == 0.1


def test_day_date_ranges(tmp_path):
    track_id = "test_day_date_ranges"
    test_track = StaticTrack(
        parameters={
            "integration-ratios": {
                "system": {"corpora": {"system-logs": 0.5}},
                "agent": {"corpora": {"agent-logs": 0.5}},
            },
            "raw-data-volume-per-day": "0.1MB",
            "max-generated-corpus-size": "0.3MB",
            "track-id": track_id,
            # run for 3d which means 0.3mb in total
            "start-date": "now-7d",
            "end-date": "now-4d",
            "sample-size": 10,
            "generator-batch-size": 10000,
            "data-generation-clients": 1,
        }
    )

    generate(test_track, tmp_path)
    generated_corpus = find_generated_corpus(test_track)
    lines_in_data_file = read_file(generated_corpus.documents[0].document_file)

    assert len(lines_in_data_file) == 464
    assert generated_corpus.documents[0].number_of_documents == 232
    assert_rally_properties(lines_in_data_file)

    doc_size = sum([doc["rally"]["doc_size"] for doc in docs(lines_in_data_file)])
    assert round(doc_size / 1024 / 1024, 1) == 0.3


def test_minute_date_ranges(tmp_path):
    track_id = "test_minute_date_ranges"
    test_track = StaticTrack(
        parameters={
            "integration-ratios": {
                "system": {"corpora": {"system-logs": 0.5}},
                "agent": {"corpora": {"agent-logs": 0.5}},
            },
            "raw-data-volume-per-day": "24MB",
            "max-generated-corpus-size": "24MB",
            "track-id": track_id,
            # run for 6m which means 0.1mb in total
            "start-date": "now",
            "end-date": "now+6m",
            "sample-size": 10,
            "generator-batch-size": 10000,
            "data-generation-clients": 1,
        }
    )

    generate(test_track, tmp_path)
    generated_corpus = find_generated_corpus(test_track)
    lines_in_data_file = read_file(generated_corpus.documents[0].document_file)

    assert len(lines_in_data_file) == 2776
    assert generated_corpus.documents[0].number_of_documents == 1388
    assert_rally_properties(lines_in_data_file)

    message_size = sum(
        [doc["rally"]["message_size"] for doc in docs(lines_in_data_file)]
    )
    assert round(message_size / 1024 / 1024, 1) == 0.1


def test_no_integration_ratios(tmp_path):
    with pytest.raises(DataError) as data_error:
        track_id = "test_data_errors"
        test_track = StaticTrack(
            parameters={
                # no corpus ratios set
                "raw-data-volume-per-day": "24MB",
                "max-generated-corpus-size": "24MB",
                "track-id": track_id,
                "generator-batch-size": 10000,
                "data-generation-clients": 1,
            }
        )
        generate(test_track, tmp_path)

    assert (
        data_error.value.message
        == "Parameter source for operation 'generate-data' did not provide the mandatory "
        "parameter 'integration-ratios'. Add it to your parameter source and try again."
    )


def test_invalid_corpus(tmp_path):
    with pytest.raises(RallyAssertionError) as rally_assertion_error:
        track_id = "test_data_errors"
        test_track = StaticTrack(
            parameters={
                "integration-ratios": {
                    "does-not-exist": {"corpora": {"does-not-exist-logs": 0.5}},
                    "agent": {"corpora": {"agent-logs": 0.5}},
                },
                "raw-data-volume-per-day": "24MB",
                "max-generated-corpus-size": "24MB",
                "track-id": track_id,
                "generator-batch-size": 10000,
                "data-generation-clients": 1,
            }
        )
        generate(test_track, tmp_path)

    assert (
        rally_assertion_error.value.message
        == "Corpus [does-not-exist-logs] is defined for data generation in "
        "integration [does-not-exist] but is not present in track"
    )


def test_invalid_integration_ratios(tmp_path):
    with pytest.raises(RallyAssertionError) as rally_assertion_error:
        track_id = "test_data_errors"
        test_track = StaticTrack(
            parameters={
                "integration-ratios": {
                    "system": {"corpora": {"system-logs": 0.3}},
                    "agent": {"corpora": {"agent-logs": 0.5}},
                },
                "raw-data-volume-per-day": "24MB",
                "max-generated-corpus-size": "24MB",
                "track-id": track_id,
                "generator-batch-size": 10000,
                "data-generation-clients": 1,
            }
        )
        generate(test_track, tmp_path)

    assert (
        rally_assertion_error.value.message
        == "Corpora ratios must total 1.0 - total is [0.8]"
    )


def test_missing_track_id(tmp_path):
    with pytest.raises(KeyError):
        test_track = StaticTrack(
            parameters={
                "integration-ratios": {
                    "system": {"corpora": {"system-logs": 0.5}},
                    "agent": {"corpora": {"agent-logs": 0.5}},
                },
                "raw-data-volume-per-day": "24MB",
                "max-generated-corpus-size": "24MB",
                "generator-batch-size": 10000,
                "data-generation-clients": 1,
            }
        )
        generate(test_track, tmp_path)


def test_missing_max_raw_data_volume_per_day(tmp_path):
    with pytest.raises(DataError) as data_error:
        track_id = "test_data_errors"
        test_track = StaticTrack(
            parameters={
                "integration-ratios": {
                    "system": {"corpora": {"system-logs": 0.5}},
                    "agent": {"corpora": {"agent-logs": 0.5}},
                },
                "track-id": track_id,
                "max-generated-corpus-size": "24MB",
                "generator-batch-size": 10000,
                "data-generation-clients": 1,
            }
        )
        generate(test_track, tmp_path)

    assert (
        data_error.value.message
        == "Parameter source for operation 'generate-data' did not provide the mandatory "
        "parameter 'raw-data-volume-per-day'. Add it to your parameter source and try "
        "again."
    )


def test_missing_max_generated_corpus_size(tmp_path):
    with pytest.raises(DataError) as data_error:
        track_id = "test_data_errors"
        test_track = StaticTrack(
            parameters={
                "integration-ratios": {
                    "system": {"corpora": {"system-logs": 0.5}},
                    "agent": {"corpora": {"agent-logs": 0.5}},
                },
                "track-id": track_id,
                "raw-data-volume-per-day": "24MB",
                "generator-batch-size": 10000,
                "data-generation-clients": 1,
            }
        )
        generate(test_track, tmp_path)

    assert (
        data_error.value.message
        == "Parameter source for operation 'generate-data' did not provide the mandatory "
        "parameter 'max-generated-corpus-size'. Add it to your parameter source and "
        "try again."
    )


def test_invalid_dates(tmp_path):
    with pytest.raises(TimeParsingError):
        test_track = StaticTrack(
            parameters={
                "integration-ratios": {"kafka": {"corpora": {"kafka-logs": 1.0}}},
                "exclude-properties": {"random": ["random"]},
                "track-id": "test_processed_file_read",
                "start-date": "wednesday",
                "raw-data-volume-per-day": "0.1MB",
                "max-generated-corpus-size": "0.1MB",
                "generator-batch-size": 10000,
                "data-generation-clients": 1,
            }
        )
        generate(test_track, tmp_path)

    with pytest.raises(TimeParsingError):
        test_track = StaticTrack(
            parameters={
                "integration-ratios": {"kafka": {"corpora": {"kafka-logs": 1.0}}},
                "exclude-properties": {"random": ["random"]},
                "track-id": "test_processed_file_read",
                "end-date": "wednesday",
                "raw-data-volume-per-day": "0.1MB",
                "max-generated-corpus-size": "0.1MB",
                "generator-batch-size": 10000,
                "data-generation-clients": 1,
            }
        )
        generate(test_track, tmp_path)

    # start greater than end
    with pytest.raises(TrackConfigError):
        test_track = StaticTrack(
            parameters={
                "integration-ratios": {"kafka": {"corpora": {"kafka-logs": 1.0}}},
                "exclude-properties": {"random": ["random"]},
                "track-id": "test_processed_file_read",
                "raw-data-volume-per-day": "0.1MB",
                "start-date": "2020-09-30:00:00:00",
                "end-date": "2020-08-01:00:00:00",
                "max-generated-corpus-size": "0.1MB",
                "generator-batch-size": 10000,
                "data-generation-clients": 1,
            }
        )

        generate(test_track, tmp_path)


def test_consistent_data_generation(tmp_path):
    def generate_corpus(ratios, seed, id):
        root_path = os.path.join(tmp_path, f"id_{id}")
        test_track = StaticTrack(
            parameters={
                "integration-ratios": {
                    "system": {"corpora": {"system-logs": ratios[0]}},
                    "agent": {"corpora": {"agent-logs": ratios[1]}},
                    "kafka": {"corpora": {"kafka-logs": ratios[2]}},
                },
                "raw-data-volume-per-day": "1MB",
                "max-generated-corpus-size": "1MB",
                "track-id": "test_consistent_data_generation",
                "random-seed": seed,
                "start-date": "2020-08-01:00:00:00",
                "end-date": "2020-08-31:00:00:00",
                "generator-batch-size": 10000,
                "sample-size": 10,
                "data-generation-clients": 1,
            }
        )
        generate(test_track, root_path)
        return test_track

    weights = [random.random() for _ in range(0, 3)]
    sum_of_weights = sum(weights)
    ratios = [weight / sum_of_weights for weight in weights]
    seed = random.randint(1, 1000)

    track_1 = generate_corpus(ratios, seed, id=1)
    track_2 = generate_corpus(ratios, seed, id=2)

    corpus_1 = find_generated_corpus(track_1)
    corpus_2 = find_generated_corpus(track_2)

    lines_in_data_file_1 = read_file(corpus_1.documents[0].document_file)
    lines_in_data_file_2 = read_file(corpus_2.documents[0].document_file)

    assert len(lines_in_data_file_1) == len(lines_in_data_file_2)
    assert lines_in_data_file_1 == lines_in_data_file_2


def test_undocumented_params(tmp_path):
    # the largest range here should be used for generation i.e. now-1h to now+1hr
    track_id = "test_undocumented_params"
    test_track = StaticTrack(
        parameters={
            "raw-data-volume-per-day": "2.4MB",
            "max-generated-corpus-size": "100MB",
            "track-id": track_id,
            "integration-ratios": {
                "system": {"corpora": {"system-logs": 0.5}},
                "agent": {"corpora": {"agent-logs": 0.5}},
            },
            "start-date": "now",
            "end-date": "now+1h",
            "bulk-start-date": "now-1h",
            "bulk-end-date": "now",
            "sample-size": 10,
            "generator-batch-size": 10000,
            "data-generation-clients": 1,
        }
    )
    # run for 2h which means 0.1mb per hr and 0.2mb in total. The size is based on the raw data volume but capped by
    # the total json capped by the max-generated-corpus - in this case sufficiently large to generate the required
    # volume
    generate(test_track, tmp_path)

    generated_corpus = find_generated_corpus(test_track)

    lines_in_data_file = read_file(generated_corpus.documents[0].document_file)
    assert len(lines_in_data_file) == 5552
    message_size = sum(
        [doc["rally"]["message_size"] for doc in docs(lines_in_data_file)]
    )
    assert round(message_size / 1024 / 1024, 1) == 0.2


def test_skip_data_generation(tmp_path):
    track_id = "test_undocumented_params"
    test_track = StaticTrack(
        parameters={
            "raw-data-volume-per-day": "2.4MB",
            "max-generated-corpus-size": "100MB",
            "track-id": track_id,
            "integration-ratios": {
                "system": {"system-logs": 0.5},
                "agent": {"agent-logs": 0.5},
            },
            "start-date": "now",
            "end-date": "now+1h",
            "bulk-start-date": "now-1h",
            "bulk-end-date": "now",
            "sample-size": 10,
            "generator-batch-size": 10000,
            "data-generation-clients": 1,
        },
        challenge_parameters={"generate-data": False},
    )

    generate(test_track, tmp_path)
    generated_corpus = find_generated_corpus(test_track)
    assert generated_corpus == None


def test_json_processor(tmp_path):
    test_track = StaticTrack(
        parameters={
            "raw-data-volume-per-day": "0.1MB",
            "max-generated-corpus-size": "0.1MB",
            "track-id": "123",
            "integration-ratios": {
                "system": {"corpora": {"system-logs": 0.5}},
                "agent": {"corpora": {"agent-logs": 0.5}},
            },
            "sample-size": 10,
            "generator-batch-size": 10000,
            "data-generation-clients": 1,
        },
        challenge_parameters={"output-folder": tmp_path},
    )

    doc = json.dumps(
        {
            "@timestamp": "2020-09-03T15:16:17.406Z",
            "id": 1,
            "message": "dummy",
            "msglen": 5,
        }
    ).encode("utf-8")
    generator = CorpusGenerator(test_track, tmp_path)
    generator.include_doc_size_with_metadata = True
    processed_doc, message_size = generator._json_processor(doc, 0, "test-corpus")
    assert message_size == 5
    assert (
        json.dumps(processed_doc)
        == '{"@timestamp": "2020-09-03T15:16:17.406Z", "id": 1, "message": "dummy", "rally":'
        ' {"message_size": 5, "doc_size": 66,'
        ' "doc_size_with_meta": 131, '
        '"markers": "-0000000010000000010000000002800000000620000000063"}}'
    )

    doc = json.dumps({"@timestamp": "2020-09-03T15:16:17.406Z", "id": 1}).encode(
        "utf-8"
    )
    processed_doc, message_size = generator._json_processor(doc, 0, "test-corpus")
    assert (
        json.dumps(processed_doc)
        == '{"@timestamp": "2020-09-03T15:16:17.406Z", "id": 1, "rally": '
        '{"message_size": 0, '
        '"doc_size": 48, "doc_size_with_meta": 113, '
        '"markers": "-00000000100000000100000000028000000004e000000004f"}}'
    )


def test_serialized_doc_markers():
    test_data = [
        # example doc with placeholder present -- most integration
        {
            "raw_doc": '{"container": {"name": "k8s_nginx-system_nginx-system-green-deployment-84c89bf49d-nfmvp_green_edb6d44b-d265-11ea-915e-42010a800009_0", "image": {"name": "sha256:3fd39c2bfa01412c773dd0910c871775a09f4ff7fa0028b3394f3a2313210260"}, "id": "f03d7d7c62cbb100eb2e9929a30dd567b1e82a276d75fb8be80fe9afd4ef0dba", "labels": {"io_kubernetes_pod_namespace": "green", "io_kubernetes_pod_uid": "edb6d44b-d265-11ea-915e-42010a800009", "maintainer": "Evan Wies <evan@neomantra.net>", "annotation_io_kubernetes_pod_terminationGracePeriod": "30", "io_kubernetes_container_logpath": "/var/log/pods/green_nginx-system-green-deployment-84c89bf49d-nfmvp_edb6d44b-d265-11ea-915e-42010a800009/nginx-system/0.log", "io_kubernetes_sandbox_id": "2337b9216097951a2ef8af32e7f4fb49070f11815b2419e8e089f3e9d5a00bc1", "org_label-schema_schema-version": "= 1.0     org.label-schema.name=CentOS Base Image     org.label-schema.vendor=CentOS     org.label-schema.license=GPLv2     org.label-schema.build-date=20180402", "resty_rpm_version": "1.13.6.2-1.el7.centos", "io_kubernetes_container_name": "nginx-system", "annotation_io_kubernetes_container_hash": "5acfc3e6", "annotation_io_kubernetes_container_terminationMessagePath": "/dev/termination-log", "resty_rpm_arch": "x86_64", "io_kubernetes_pod_name": "nginx-system-green-deployment-84c89bf49d-nfmvp", "annotation_io_kubernetes_container_terminationMessagePolicy": "File", "annotation_io_kubernetes_container_ports": "[{\\"name\\":\\"status\\",\\"containerPort\\":8080,\\"protocol\\":\\"TCP\\"},{\\"name\\":\\"kibana\\",\\"containerPort\\":80,\\"protocol\\":\\"TCP\\"}]", "resty_luarocks_version": "2.4.4", "annotation_io_kubernetes_container_restartCount": "0", "io_kubernetes_docker_type": "container", "resty_rpm_flavor": ""}}, "log": {"file": {"path": "/var/lib/docker/containers/f03d7d7c62cbb100eb2e9929a30dd567b1e82a276d75fb8be80fe9afd4ef0dba/f03d7d7c62cbb100eb2e9929a30dd567b1e82a276d75fb8be80fe9afd4ef0dba-json.log"}, "offset": 6558093}, "kubernetes": {"namespace": "green", "container": {"name": "nginx-system", "image": "openresty/openresty:1.13.6.2-0-centos"}, "replicaset": {"name": "nginx-system-green-deployment-84c89bf49d"}, "labels": {"app": "nginx-system", "heartbeat_type": "http", "pod-template-hash": "84c89bf49d", "heartbeat_port": "8080"}, "pod": {"uid": "edb6d44b-d265-11ea-915e-42010a800009", "name": "nginx-system-green-deployment-84c89bf49d-nfmvp"}, "node": {"name": "gke-demo-elastic-co-default-pool-d2239e75-ktze"}}, "host": {"mac": ["0a:1a:9a:e9:41:b6"], "hostname": "filebeat-demo-green-l6sb5", "architecture": "x86_64", "containerized": false, "ip": ["10.12.8.81"], "name": "filebeat-demo-green-l6sb5", "os": {"platform": "centos", "family": "redhat", "version": "7 (Core)", "kernel": "4.14.138+", "name": "CentOS Linux", "codename": "Core"}, "id": "83a8f1f835d84a9a9bf5417cecaf0c8e"}, "cloud": {"project": {"id": "elastic-product"}, "provider": "gcp", "instance": {"name": "gke-demo-elastic-co-default-pool-d2239e75-ktze", "id": "4185994108039115136"}, "availability_zone": "us-central1-a", "machine": {"type": "n1-standard-32"}}, "agent": {"hostname": "filebeat-demo-green-l6sb5", "name": "filebeat-demo-green-l6sb5", "ephemeral_id": "f4aa9965-b74b-4a14-ad52-b8449d0ba937", "version": "7.8.0", "type": "filebeat", "id": "596fa15f-7bcc-4f4e-b988-b2a12c5e76bc"}, "stream": "stdout", "@timestamp": "2020-09-13T16:24:53.000Z", "event": {"timezone": "+00:00", "module": "nginx", "dataset": "nginx.access"}, "fileset": {"name": "access"}, "input": {"type": "docker"}, "service": {"type": "nginx"}, "ecs": {"version": "1.5.0"}, "message": "134.68.249.190 - danielle15 [_RALLYTS023<%d/%b/%Y:%H:%M:%S +0000>] \\"GET / HTTP/1.1\\" 200 649 \\"\\" \\"Elastic-Heartbeat/7.8.0 (linux; amd64; f79387d32717d79f689d94fda1ec80b2cf285d30; 2020-06-14 17:31:16 +0000 UTC)\\"", "data_stream": {"type": "logs", "namespace": "default", "dataset": "nginx.access"}, "rally": {"message_size": 196, "doc_size": 400}}',
            "expected_marker": "0000000e0b0000000d010000000d190000000f350000000f38",
            "whole_rallyts": "_RALLYTS023<%d/%b/%Y:%H:%M:%S +0000>",
            "rallyts": "%d/%b/%Y:%H:%M:%S +0000",
            "@timestamp": "2020-09-13T16:24:53.000Z",
            "msgsize": 196,
            "placeholder": True,
        },
        # doc without placeholder -- application-logs, redis-slowlog-logs
        {
            "raw_doc": '{"container": {"name": "k8s_nginx-system_nginx-system-green-deployment-84c89bf49d-nfmvp_green_edb6d44b-d265-11ea-915e-42010a800009_0", "image": {"name": "sha256:3fd39c2bfa01412c773dd0910c871775a09f4ff7fa0028b3394f3a2313210260"}, "id": "f03d7d7c62cbb100eb2e9929a30dd567b1e82a276d75fb8be80fe9afd4ef0dba", "labels": {"io_kubernetes_pod_namespace": "green", "io_kubernetes_pod_uid": "edb6d44b-d265-11ea-915e-42010a800009", "maintainer": "Evan Wies <evan@neomantra.net>", "annotation_io_kubernetes_pod_terminationGracePeriod": "30", "io_kubernetes_container_logpath": "/var/log/pods/green_nginx-system-green-deployment-84c89bf49d-nfmvp_edb6d44b-d265-11ea-915e-42010a800009/nginx-system/0.log", "io_kubernetes_sandbox_id": "2337b9216097951a2ef8af32e7f4fb49070f11815b2419e8e089f3e9d5a00bc1", "org_label-schema_schema-version": "= 1.0     org.label-schema.name=CentOS Base Image     org.label-schema.vendor=CentOS     org.label-schema.license=GPLv2     org.label-schema.build-date=20180402", "resty_rpm_version": "1.13.6.2-1.el7.centos", "io_kubernetes_container_name": "nginx-system", "annotation_io_kubernetes_container_hash": "5acfc3e6", "annotation_io_kubernetes_container_terminationMessagePath": "/dev/termination-log", "resty_rpm_arch": "x86_64", "io_kubernetes_pod_name": "nginx-system-green-deployment-84c89bf49d-nfmvp", "annotation_io_kubernetes_container_terminationMessagePolicy": "File", "annotation_io_kubernetes_container_ports": "[{\\"name\\":\\"status\\",\\"containerPort\\":8080,\\"protocol\\":\\"TCP\\"},{\\"name\\":\\"kibana\\",\\"containerPort\\":80,\\"protocol\\":\\"TCP\\"}]", "resty_luarocks_version": "2.4.4", "annotation_io_kubernetes_container_restartCount": "0", "io_kubernetes_docker_type": "container", "resty_rpm_flavor": ""}}, "log": {"file": {"path": "/var/lib/docker/containers/f03d7d7c62cbb100eb2e9929a30dd567b1e82a276d75fb8be80fe9afd4ef0dba/f03d7d7c62cbb100eb2e9929a30dd567b1e82a276d75fb8be80fe9afd4ef0dba-json.log"}, "offset": 6558093}, "kubernetes": {"namespace": "green", "container": {"name": "nginx-system", "image": "openresty/openresty:1.13.6.2-0-centos"}, "replicaset": {"name": "nginx-system-green-deployment-84c89bf49d"}, "labels": {"app": "nginx-system", "heartbeat_type": "http", "pod-template-hash": "84c89bf49d", "heartbeat_port": "8080"}, "pod": {"uid": "edb6d44b-d265-11ea-915e-42010a800009", "name": "nginx-system-green-deployment-84c89bf49d-nfmvp"}, "node": {"name": "gke-demo-elastic-co-default-pool-d2239e75-ktze"}}, "host": {"mac": ["0a:1a:9a:e9:41:b6"], "hostname": "filebeat-demo-green-l6sb5", "architecture": "x86_64", "containerized": false, "ip": ["10.12.8.81"], "name": "filebeat-demo-green-l6sb5", "os": {"platform": "centos", "family": "redhat", "version": "7 (Core)", "kernel": "4.14.138+", "name": "CentOS Linux", "codename": "Core"}, "id": "83a8f1f835d84a9a9bf5417cecaf0c8e"}, "cloud": {"project": {"id": "elastic-product"}, "provider": "gcp", "instance": {"name": "gke-demo-elastic-co-default-pool-d2239e75-ktze", "id": "4185994108039115136"}, "availability_zone": "us-central1-a", "machine": {"type": "n1-standard-32"}}, "agent": {"hostname": "filebeat-demo-green-l6sb5", "name": "filebeat-demo-green-l6sb5", "ephemeral_id": "f4aa9965-b74b-4a14-ad52-b8449d0ba937", "version": "7.8.0", "type": "filebeat", "id": "596fa15f-7bcc-4f4e-b988-b2a12c5e76bc"}, "stream": "stdout", "@timestamp": "2020-09-13T16:24:53.000Z", "event": {"timezone": "+00:00", "module": "nginx", "dataset": "nginx.access"}, "fileset": {"name": "access"}, "input": {"type": "docker"}, "service": {"type": "nginx"}, "ecs": {"version": "1.5.0"}, "message": "134.68.249.190 - danielle15 [13/Sep/2020:16:24:53 +0000] \\"GET / HTTP/1.1\\" 200 649 \\"\\" \\"Elastic-Heartbeat/7.8.0 (linux; amd64; f79387d32717d79f689d94fda1ec80b2cf285d30; 2020-06-14 17:31:16 +0000 UTC)\\"", "data_stream": {"type": "logs", "namespace": "default", "dataset": "nginx.access"}, "rally": {"message_size": 196, "doc_size": 400}}',
            "expected_marker": "-0000000010000000d010000000d190000000f2b0000000f2e",
            "@timestamp": "2020-09-13T16:24:53.000Z",
            "msgsize": 196,
            "placeholder": False,
        },
    ]

    for data in test_data:
        raw_doc = data["raw_doc"]
        doc = json.loads(raw_doc)

        CorpusGenerator._append_doc_markers(doc)
        new_raw_doc = json.dumps(doc)
        assert (
            json.dumps(doc)
            == raw_doc[:-2] + f', "markers": ' + f'"{data["expected_marker"]}"' + "}}"
        )

        assert doc["rally"]["markers"] == data["expected_marker"]

        msglen_value_start_pos = int(
            new_raw_doc[MagicNumbers.MSGLEN_BEGIN_IDX : MagicNumbers.MSGLEN_END_IDX], 16
        )
        msglen_value_end_pos = int(
            new_raw_doc[MagicNumbers.MSGLEN_END_IDX : MagicNumbers.MSGLEN_END_IDX + 10],
            16,
        )

        msgsize = int(new_raw_doc[msglen_value_start_pos:msglen_value_end_pos], 10)
        assert msgsize == data["msgsize"]

        if data["placeholder"]:
            rallyts_start_pos = int(
                new_raw_doc[MagicNumbers.RALLYTS_BEGIN_IDX : MagicNumbers.TS_BEGIN_IDX],
                16,
            )
            rallyts_len = int(
                new_raw_doc[
                    rallyts_start_pos
                    + MagicNumbers.RALLYTS_LEN : rallyts_start_pos
                    + MagicNumbers.RALLYTSDATA_LEN_END
                ],
                10,
            )
            ts_format = new_raw_doc[
                rallyts_start_pos
                + MagicNumbers.RALLYTS_FORMAT_BEGIN : rallyts_start_pos
                + MagicNumbers.RALLYTS_FORMAT_BEGIN
                + rallyts_len
            ]
            whole_rallyts = new_raw_doc[
                rallyts_start_pos : rallyts_start_pos
                + MagicNumbers.RALLYTS_FORMAT_BEGIN
                + rallyts_len
                + 1
            ]

            assert whole_rallyts == data["whole_rallyts"]
            assert ts_format == data["rallyts"]
        else:
            ts_value_start_pos = int(
                new_raw_doc[MagicNumbers.TS_BEGIN_IDX : MagicNumbers.TS_END_IDX], 16
            )
            ts_value_end_pos = int(
                new_raw_doc[MagicNumbers.TS_END_IDX : MagicNumbers.MSGLEN_BEGIN_IDX], 16
            )

            timestamp = new_raw_doc[ts_value_start_pos:ts_value_end_pos]
            assert timestamp == data["@timestamp"]

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
import math
import re

from esrally.exceptions import InvalidSyntax


def calculate_integration_ratios(corpus_counts):
    total_docs = sum(corpus_counts.values())
    corpora_ratios = {}
    # calculate true ratios based on docs required for each corpus
    for corpus_name, doc_count in corpus_counts.items():
        corpora_ratios[corpus_name] = doc_count / total_docs
    return corpora_ratios


def calculate_corpus_counts(
    corpus_stats, corpora_ratios, required_raw_volume_gb, max_generation_size_gb=0
):
    """
    Calculates the required document counts to satisfy the specified required_raw_volume_gb and specified ratios.
    Scales these document counts to the limit imposed by max_generation_size_gb.
    :param corpus_stats: A map of statistics for a set of corpora, where each key represents a corpus name and the value
                         the statistics. The statistics "raw_json_ratio" and "avg_doc_size_with_meta" are required
                         for each corpus.
    :param corpora_ratios: Ratios of the corpora where keys are corpus names and values a ratio 0-1. Sum of values must
                           equal 1.
    :param required_raw_volume_gb: Required GB of raw data
    :param max_generation_size_gb: Upper limit in GB of documents (JSON) that can be used. Counts will be scaled to
                                   respect required_raw_volume_gb but be limited by this value. 0 means no limit is
                                   applied (default)
    :return: (dict) dictionary of counts, where they keys are corpus names and the values doc counts.
    """
    corpora_doc_counts = {}
    # we calculate the required gb of json to satisfy the requested required_raw_volume of raw data according to
    # the ratios
    total_generated_volume_bytes = required_raw_volume_gb * 1024 * 1024 * 1024
    required_corpus_bytes = {}
    for corpus_name, ratio in corpora_ratios.items():
        required_corpus_bytes[corpus_name] = (
            ratio
            * total_generated_volume_bytes
            * corpus_stats[corpus_name]["raw_json_ratio"]
        )
    total_required_bytes = sum(required_corpus_bytes.values())
    # we don't want to generate more than we need so take the min
    if max_generation_size_gb > 0:
        actual_generation_size = min(
            total_required_bytes, max_generation_size_gb * 1024 * 1024 * 1024
        )
    else:
        actual_generation_size = total_required_bytes
    # we scale to the amount requested or we'd generate a lot more than max_generation_size per day
    for corpus_name, required_bytes in required_corpus_bytes.items():
        actual_bytes = (required_bytes / total_required_bytes) * actual_generation_size
        corpora_doc_counts[corpus_name] = math.ceil(
            actual_bytes / corpus_stats[corpus_name]["avg_doc_size_with_meta"]
        )
    return corpora_doc_counts


def bounds(total_docs, client_index, num_clients, ensure_even=False):
    docs_per_client = math.floor(total_docs / num_clients)
    if ensure_even and docs_per_client % 2 == 1:
        docs_per_client += 1
    if docs_per_client == 0:
        docs_per_client = 1
    start_offset_docs = math.floor(docs_per_client * client_index)
    if start_offset_docs >= total_docs:
        return 0, 0
    end_offset_docs = total_docs
    if client_index != num_clients - 1:
        end_offset_docs = math.floor(docs_per_client * (client_index + 1))
    num_docs = end_offset_docs - start_offset_docs
    return start_offset_docs, num_docs


def convert_to_gib(volume_size: str) -> int:
    """
    Convert a human string for disk size to pure integer gigabytes.
    :param volume_size: string of the form "<integer size><binary prefix><?unit of information>" like "2TB".
                        Unit of information is optional, values like "2G" are also accepted.
    :return: (float) volume size in gigabytes
    """

    m = re.search(r"([0-9.]+)(.+)", volume_size)
    if not m:
        raise InvalidSyntax("Missing or unsupported size [%s]", volume_size)

    size = float(m.group(1))
    unit = m.group(2)

    try:
        return size * (1024 ** SIZE_UNITS[unit])
    except KeyError:
        raise InvalidSyntax("Missing or unsupported size [%s]", volume_size)


# we deliberately don't support less than a MB
SIZE_UNITS = {"M": -1, "MB": -1, "G": 0, "GB": 0, "T": 1, "TB": 1, "P": 2, "PB": 2}

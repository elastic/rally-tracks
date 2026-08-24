# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import json
import pathlib

import jinja2

TRACK_DIR = pathlib.Path(__file__).parents[1]


def render_operations(**params):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(TRACK_DIR / "operations")))
    rendered = env.get_template("default.json").render(**params)
    return json.loads(f"[{rendered}]")


def render_challenge(**params):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(TRACK_DIR / "challenges")))
    rendered = env.get_template("default.json").render(**params)
    return json.loads(rendered)


def render_mapping(**params):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(TRACK_DIR)))
    rendered = env.get_template("index.json").render(**params)
    return json.loads(rendered)


class TestRenderedOperations:
    def test_defaults(self):
        ops = render_operations()
        assert len(ops) == 1
        op = ops[0]
        assert op["name"] == "knn-search-100-256"
        assert op["operation-type"] == "search"
        assert op["k"] == 100
        assert op["num-candidates"] == 256
        assert op["oversample"] is None
        assert op["request-timeout"] == 600

    def test_custom_k_and_num_candidates_via_knn_params(self):
        ops = render_operations(knn_k=50, knn_num_candidates=512)
        op = ops[0]
        assert op["name"] == "knn-search-50-512"
        assert op["k"] == 50
        assert op["num-candidates"] == 512

    def test_search_ops_single_pair(self):
        ops = render_operations(search_ops=[(10, 50)])
        assert len(ops) == 1
        op = ops[0]
        assert op["name"] == "knn-search-10-50"
        assert op["k"] == 10
        assert op["num-candidates"] == 50

    def test_search_ops_multiple_pairs(self):
        ops = render_operations(search_ops=[(100, 256), (10, 50)])
        assert len(ops) == 2
        names = [o["name"] for o in ops]
        assert "knn-search-100-256" in names
        assert "knn-search-10-50" in names

    def test_oversample(self):
        ops = render_operations(oversample=1.5)
        assert ops[0]["oversample"] == 1.5

    def test_custom_request_timeout(self):
        ops = render_operations(search_request_timeout=300)
        assert ops[0]["request-timeout"] == 300


class TestRenderedChallenge:
    def _schedule_names(self, challenge):
        return [step.get("name") for step in challenge["schedule"]]

    def test_search_tasks_always_present(self):
        challenge = render_challenge()
        names = self._schedule_names(challenge)
        assert "knn-search-100-256" in names
        assert "knn-search-100-256-multi-client" in names

    def test_pre_merge_recall_always_present(self):
        challenge = render_challenge()
        names = self._schedule_names(challenge)
        assert "knn-recall-100-256" in names

    def test_pre_merge_recall_tagged_search(self):
        challenge = render_challenge()
        recall_step = next(s for s in challenge["schedule"] if s.get("name") == "knn-recall-100-256")
        assert "search" in recall_step["tags"]
        assert "search-after-force-merge" not in recall_step["tags"]

    def test_default_includes_force_merge_and_post_merge_search(self):
        challenge = render_challenge()
        names = self._schedule_names(challenge)
        assert "knn-search-100-256-force-merge" in names
        assert "knn-search-100-256-multi-client-force-merge" in names

    def test_post_merge_recall_present_with_force_merge(self):
        challenge = render_challenge()
        names = self._schedule_names(challenge)
        assert "knn-recall-100-256-force-merge" in names

    def test_post_merge_recall_tagged_search_after_force_merge(self):
        challenge = render_challenge()
        recall_step = next(s for s in challenge["schedule"] if s.get("name") == "knn-recall-100-256-force-merge")
        assert "search-after-force-merge" in recall_step["tags"]

    def test_serverless_skips_force_merge_phase(self):
        challenge = render_challenge(build_flavor="serverless")
        names = self._schedule_names(challenge)
        assert "knn-search-100-256" in names
        assert "knn-recall-100-256" in names
        assert "knn-search-100-256-force-merge" not in names
        assert "knn-search-100-256-multi-client-force-merge" not in names
        assert "knn-recall-100-256-force-merge" not in names

    def test_explicit_include_force_merge_overrides_serverless(self):
        challenge = render_challenge(build_flavor="serverless", include_force_merge=True)
        names = self._schedule_names(challenge)
        assert "knn-search-100-256-force-merge" in names
        assert "knn-recall-100-256-force-merge" in names

    def test_recall_params(self):
        challenge = render_challenge()
        recall_step = next(s for s in challenge["schedule"] if s.get("name") == "knn-recall-100-256")
        op = recall_step["operation"]
        assert op["k"] == 100
        assert op["num-candidates"] == 256
        assert op["oversample"] is None
        assert op["request-timeout"] == 600

    def test_custom_recall_params(self):
        challenge = render_challenge(knn_k=50, knn_num_candidates=512, recall_request_timeout=300)
        recall_step = next(s for s in challenge["schedule"] if s.get("name") == "knn-recall-50-512")
        op = recall_step["operation"]
        assert op["k"] == 50
        assert op["num-candidates"] == 512
        assert op["request-timeout"] == 300

    def test_search_ops_generates_named_steps(self):
        challenge = render_challenge(search_ops=[(10, 50), (100, 256)])
        names = self._schedule_names(challenge)
        assert "knn-search-10-50" in names
        assert "knn-search-100-256" in names
        assert "knn-recall-10-50" in names
        assert "knn-recall-100-256" in names

    def test_post_ingest_sleep_absent_by_default(self):
        challenge = render_challenge()
        names = self._schedule_names(challenge)
        assert "post-ingest-sleep-after-index" not in names

    def test_post_ingest_sleep_present_when_enabled(self):
        challenge = render_challenge(post_ingest_sleep=True)
        names = self._schedule_names(challenge)
        assert "post-ingest-sleep-after-index" in names
        sleep_step = next(s for s in challenge["schedule"] if s.get("name") == "post-ingest-sleep-after-index")
        assert sleep_step["operation"]["duration"] == 30

    def test_post_ingest_sleep_custom_duration(self):
        challenge = render_challenge(post_ingest_sleep=True, post_ingest_sleep_duration=60)
        sleep_step = next(s for s in challenge["schedule"] if s.get("name") == "post-ingest-sleep-after-index")
        assert sleep_step["operation"]["duration"] == 60

    def test_post_merge_sleep_present_with_force_merge(self):
        challenge = render_challenge(post_ingest_sleep=True)
        names = self._schedule_names(challenge)
        assert "post-ingest-sleep" in names

    def test_custom_bulk_params(self):
        challenge = render_challenge(bulk_size=200, bulk_indexing_clients=8, bulk_warmup=10)
        index_step = next(s for s in challenge["schedule"] if s.get("name") == "index-append")
        assert index_step["operation"]["bulk-size"] == 200
        assert index_step["clients"] == 8
        assert index_step["warmup-time-period"] == 10

    def test_custom_search_clients(self):
        challenge = render_challenge(search_clients=4)
        multi_step = next(s for s in challenge["schedule"] if s.get("name") == "knn-search-100-256-multi-client")
        assert multi_step["clients"] == 4

    def test_wait_steps_have_retry_config(self):
        challenge = render_challenge()
        wait_step = next(s for s in challenge["schedule"] if s.get("name") == "wait-until-merges-finish-after-index")
        op = wait_step["operation"]
        assert op["retries"] == 1440
        assert op["retry-on-error"] is True
        assert op["retry-wait-period"] == 30

    def test_wait_after_force_merge_in_reporting(self):
        challenge = render_challenge()
        wait_step = next(s for s in challenge["schedule"] if s.get("name") == "wait-until-merges-finish")
        assert wait_step["operation"]["include-in-reporting"] is True


class TestRenderedMapping:
    def _emb(self, mapping):
        return mapping["mappings"]["properties"]["emb"]

    def _index_settings(self, mapping):
        return mapping["settings"]["index"]

    def test_defaults(self):
        mapping = render_mapping()
        emb = self._emb(mapping)
        assert emb["index_options"]["type"] == "bbq_disk"
        assert emb["similarity"] == "cosine"
        assert "element_type" not in emb

    def test_custom_index_type(self):
        mapping = render_mapping(vector_index_type="int8_hnsw")
        assert self._emb(mapping)["index_options"]["type"] == "int8_hnsw"

    def test_custom_similarity(self):
        mapping = render_mapping(vector_similarity="dot_product")
        assert self._emb(mapping)["similarity"] == "dot_product"

    def test_element_type_when_set(self):
        mapping = render_mapping(vector_index_element_type="bfloat16")
        assert self._emb(mapping)["element_type"] == "bfloat16"

    def test_on_disk_rescore_absent_by_default(self):
        mapping = render_mapping()
        assert "on_disk_rescore" not in self._emb(mapping)["index_options"]

    def test_on_disk_rescore_when_set(self):
        mapping = render_mapping(vector_index_on_disk_rescore=False)
        assert self._emb(mapping)["index_options"]["on_disk_rescore"] is False

    def test_hnsw_tuning_params(self):
        mapping = render_mapping(hnsw_m=16, hnsw_ef_construction=200, bits=4)
        opts = self._emb(mapping)["index_options"]
        assert opts["m"] == 16
        assert opts["ef_construction"] == 200
        assert opts["bits"] == 4

    def test_experimental_features_enabled_by_default(self):
        mapping = render_mapping()
        assert self._index_settings(mapping).get("dense_vector.experimental_features") is True

    def test_experimental_features_can_be_disabled(self):
        mapping = render_mapping(enable_experimental_features=False)
        assert "dense_vector.experimental_features" not in self._index_settings(mapping)

    def test_default_shard_settings(self):
        mapping = render_mapping()
        settings = self._index_settings(mapping)
        assert settings["number_of_shards"] == 1
        assert settings["number_of_replicas"] == 0

    def test_serverless_omits_shard_settings(self):
        mapping = render_mapping(build_flavor="serverless")
        settings = self._index_settings(mapping)
        assert "number_of_shards" not in settings
        assert "number_of_replicas" not in settings

    def test_index_mode_absent_by_default(self):
        mapping = render_mapping()
        assert "mode" not in self._index_settings(mapping)

    def test_index_mode_when_set(self):
        mapping = render_mapping(index_mode="logsdb")
        assert self._index_settings(mapping)["mode"] == "logsdb"

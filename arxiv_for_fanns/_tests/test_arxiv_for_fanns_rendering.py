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

SEARCH_OPS = [(100, 128), (100, 256), (100, 512), (10, 64), (10, 128), (10, 256), (10, 512)]


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
    def _op(self, ops, name):
        return next(o for o in ops if o["name"] == name)

    def test_generates_one_search_and_one_recall_per_pair(self):
        ops = render_operations()
        assert len(ops) == len(SEARCH_OPS) * 2

    def test_all_search_operations_present(self):
        ops = render_operations()
        names = {o["name"] for o in ops}
        for k, nc in SEARCH_OPS:
            assert f"knn-search-{k}-{nc}" in names

    def test_all_recall_operations_present(self):
        ops = render_operations()
        names = {o["name"] for o in ops}
        for k, nc in SEARCH_OPS:
            assert f"knn-recall-{k}-{nc}" in names

    def test_search_operation_fields(self):
        ops = render_operations()
        op = self._op(ops, "knn-search-100-256")
        assert op["operation-type"] == "search"
        assert op["k"] == 100
        assert op["num-candidates"] == 256
        assert op["oversample"] is None
        assert op["request-timeout"] == 600

    def test_recall_operation_fields(self):
        ops = render_operations()
        op = self._op(ops, "knn-recall-10-64")
        assert op["operation-type"] == "knn-recall"
        assert op["k"] == 10
        assert op["num-candidates"] == 64
        assert op["oversample"] is None
        assert op["request-timeout"] == 600
        assert op["include-in-reporting"] is False

    def test_ground_truth_k_is_max_k_for_all_recall_ops(self):
        ops = render_operations()
        max_k = max(k for k, _ in SEARCH_OPS)
        for k, nc in SEARCH_OPS:
            op = self._op(ops, f"knn-recall-{k}-{nc}")
            assert op["ground-truth-k"] == max_k, f"knn-recall-{k}-{nc} has wrong ground-truth-k"

    def test_queries_file_default_in_all_ops(self):
        ops = render_operations()
        for op in ops:
            assert op["queries-file"] == "queries_emis.json.zst", f"{op['name']} missing default queries-file"

    def test_queries_file_custom_propagates_to_all_ops(self):
        ops = render_operations(queries_file="custom.json.zst")
        for op in ops:
            assert op["queries-file"] == "custom.json.zst", f"{op['name']} did not pick up custom queries-file"

    def test_queries_file_matches_challenge_parameters(self):
        """The operation param and the challenge parameters block must agree."""
        custom = "custom.json.zst"
        ops = render_operations(queries_file=custom)
        challenge = render_challenge(queries_file=custom)
        for op in ops:
            assert op["queries-file"] == challenge["parameters"]["queries_file"]

    def test_oversample_propagates_to_both_types(self):
        ops = render_operations(oversample=1.5)
        search_op = self._op(ops, "knn-search-100-256")
        recall_op = self._op(ops, "knn-recall-100-256")
        assert search_op["oversample"] == 1.5
        assert recall_op["oversample"] == 1.5

    def test_custom_search_request_timeout(self):
        ops = render_operations(search_request_timeout=300)
        op = self._op(ops, "knn-search-100-256")
        assert op["request-timeout"] == 300

    def test_custom_recall_request_timeout(self):
        ops = render_operations(recall_request_timeout=120)
        op = self._op(ops, "knn-recall-100-256")
        assert op["request-timeout"] == 120

    def test_ingest_percentage_in_recall(self):
        ops = render_operations(ingest_percentage=50)
        op = self._op(ops, "knn-recall-100-256")
        assert op["ingest-percentage"] == 50


class TestRenderedChallenge:
    def _schedule_names(self, challenge):
        return [step.get("name") for step in challenge["schedule"]]

    def test_all_search_steps_present(self):
        challenge = render_challenge()
        names = self._schedule_names(challenge)
        for k, nc in SEARCH_OPS:
            assert f"knn-search-{k}-{nc}" in names
            assert f"knn-search-{k}-{nc}-multi-client" in names

    def test_all_pre_merge_recall_steps_present(self):
        challenge = render_challenge()
        names = self._schedule_names(challenge)
        for k, nc in SEARCH_OPS:
            assert f"knn-recall-{k}-{nc}" in names

    def test_pre_merge_recall_tagged_search(self):
        challenge = render_challenge()
        recall_step = next(s for s in challenge["schedule"] if s.get("name") == "knn-recall-100-256")
        assert "search" in recall_step["tags"]
        assert "search-after-force-merge" not in recall_step["tags"]

    def test_recall_steps_reference_named_operation(self):
        challenge = render_challenge()
        recall_step = next(s for s in challenge["schedule"] if s.get("name") == "knn-recall-100-256")
        assert recall_step["operation"] == "knn-recall-100-256"

    def test_search_steps_reference_named_operation(self):
        challenge = render_challenge()
        step = next(s for s in challenge["schedule"] if s.get("name") == "knn-search-100-256")
        assert step["operation"] == "knn-search-100-256"

    def test_multi_client_step_reuses_search_operation(self):
        challenge = render_challenge()
        step = next(s for s in challenge["schedule"] if s.get("name") == "knn-search-100-256-multi-client")
        assert step["operation"] == "knn-search-100-256"

    def test_default_includes_force_merge_and_post_merge_steps(self):
        challenge = render_challenge()
        names = self._schedule_names(challenge)
        for k, nc in SEARCH_OPS:
            assert f"knn-search-{k}-{nc}-force-merge" in names
            assert f"knn-search-{k}-{nc}-multi-client-force-merge" in names
            assert f"knn-recall-{k}-{nc}-force-merge" in names

    def test_post_merge_recall_tagged_search_after_force_merge(self):
        challenge = render_challenge()
        step = next(s for s in challenge["schedule"] if s.get("name") == "knn-recall-100-256-force-merge")
        assert "search-after-force-merge" in step["tags"]

    def test_post_merge_recall_reuses_named_operation(self):
        challenge = render_challenge()
        step = next(s for s in challenge["schedule"] if s.get("name") == "knn-recall-100-256-force-merge")
        assert step["operation"] == "knn-recall-100-256"

    def test_serverless_skips_force_merge_phase(self):
        challenge = render_challenge(build_flavor="serverless")
        names = self._schedule_names(challenge)
        assert "knn-search-100-256" in names
        assert "knn-recall-100-256" in names
        assert "knn-search-100-256-force-merge" not in names
        assert "knn-recall-100-256-force-merge" not in names

    def test_explicit_include_force_merge_overrides_serverless(self):
        challenge = render_challenge(build_flavor="serverless", include_force_merge=True)
        names = self._schedule_names(challenge)
        assert "knn-search-100-256-force-merge" in names
        assert "knn-recall-100-256-force-merge" in names

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

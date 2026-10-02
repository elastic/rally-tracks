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
    rendered = env.get_template("index-vectors-only-mapping.json").render(**params)
    return json.loads(rendered)


class TestRenderedOperations:
    def test_default_search_op_omits_k_and_num_candidates(self):
        ops = render_operations()
        op = next(o for o in ops if o["name"] == "knn-search-default-default")
        assert op["operation-type"] == "search"
        assert "k" not in op
        assert "num-candidates" not in op

    def test_partial_k_only(self):
        ops = render_operations(search_ops=[(10, None)])
        op = next(o for o in ops if o["name"] == "knn-search-10-default")
        assert op["k"] == 10
        assert "num-candidates" not in op

    def test_partial_num_candidates_only(self):
        ops = render_operations(search_ops=[(None, 20)])
        op = next(o for o in ops if o["name"] == "knn-search-default-20")
        assert "k" not in op
        assert op["num-candidates"] == 20

    def test_explicit_k_and_num_candidates(self):
        ops = render_operations(search_ops=[(10, 15)])
        search = next(o for o in ops if o["name"] == "knn-search-10-15")
        recall = next(o for o in ops if o["name"] == "knn-recall-10-15")
        assert search["k"] == 10
        assert search["num-candidates"] == 15
        assert recall["k"] == 10
        assert recall["num-candidates"] == 15


class TestRenderedChallenge:
    def test_default_includes_pre_and_post_force_merge_search_tasks(self):
        challenge = render_challenge()
        names = [step.get("name") for step in challenge["schedule"]]
        assert "search-knn-10-15-single-client" in names
        assert "search-knn-10-15-single-client-force-merge" in names
        assert "force-merge-after-index" in names

    def test_serverless_skips_force_merge_and_post_merge_tasks(self):
        challenge = render_challenge(build_flavor="serverless")
        names = [step.get("name") for step in challenge["schedule"]]
        assert "search-knn-10-15-single-client" in names
        assert "force-merge-after-index" not in names
        assert "search-knn-10-15-single-client-force-merge" not in names

    def test_custom_search_ops_drive_schedule_task_names(self):
        challenge = render_challenge(search_ops=[(10, 50), (100, 150)])
        names = [step.get("name") for step in challenge["schedule"]]
        assert "search-knn-10-50-multi-client" in names
        assert "recall-knn-100-150" in names
        assert "search-knn-default-default-single-client" not in names


class TestRenderedMapping:
    def test_default_vector_index_settings(self):
        mapping = render_mapping()
        assert mapping["mappings"]["properties"]["emb"]["index_options"]["type"] == "bbq_hnsw"
        assert mapping["mappings"]["properties"]["emb"]["element_type"] == "float"

    def test_custom_vector_index_settings(self):
        mapping = render_mapping(vector_index_type="int8_hnsw", vector_index_element_type="bfloat16")
        assert mapping["mappings"]["properties"]["emb"]["index_options"]["type"] == "int8_hnsw"
        assert mapping["mappings"]["properties"]["emb"]["element_type"] == "bfloat16"

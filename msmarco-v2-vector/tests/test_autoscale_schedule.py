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
import pathlib

import jinja2

COMMON_DIR = pathlib.Path(__file__).parents[1] / "challenges" / "common"


def render(template_name, params):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(COMMON_DIR)))
    rendered = env.get_template(template_name).render(**params)
    return json.loads(f"[{rendered}]")


def render_search(params=None):
    base = {"include_initial_indexing": False}
    if params:
        base.update(params)
    return render("search-autoscale-schedule.json", base)


def render_ingest_search(params=None):
    return render("ingest-search-autoscale-schedule.json", params or {})


def render_ingest(params=None):
    return render("ingest-autoscale-schedule.json", params or {})


# --- search-autoscale-schedule.json ---


class TestSearchAutoscaleSchedule:
    def test_default_params_five_phases(self):
        steps = render_search()
        # 5 default phases × 2 query sizes (k=10, k=100) = 10 steps
        assert len(steps) == 10

    def test_default_single_element_warmup_repeats(self):
        # Template default as_warmup_time_periods=[600] applies to all 5 phases
        steps = render_search()
        assert all(s["warmup-time-period"] == 600 for s in steps)

    def test_default_single_element_time_period_repeats(self):
        # Template default as_time_periods=[1800] applies to all 5 phases
        steps = render_search()
        assert all(s["time-period"] == 1800 for s in steps)

    def test_default_single_element_throughput_is_unlimited(self):
        # Template default as_search_target_throughputs=[-1] means no throttle
        steps = render_search()
        assert all("target-throughput" not in s for s in steps)

    def test_phase_count_driven_by_as_phases(self):
        steps = render_search({"as_phases": 4, "as_search_clients": [1]})
        assert len(steps) == 8  # 4 phases × 2 query sizes

    def test_warmup_zero_clamped_to_one(self):
        steps = render_search({"as_phases": 3, "as_warmup_time_periods": [0], "as_search_clients": [1]})
        assert all(s["warmup-time-period"] == 1 for s in steps)

    def test_warmup_positive_value_preserved(self):
        steps = render_search({"as_phases": 4, "as_warmup_time_periods": [30, 0, 0, 0], "as_search_clients": [1]})
        # first phase (2 steps: s10 and s100) should keep warmup=30
        assert steps[0]["warmup-time-period"] == 30
        assert steps[1]["warmup-time-period"] == 30
        # remaining phases clamped to 1
        assert all(s["warmup-time-period"] == 1 for s in steps[2:])

    def test_single_element_time_periods_repeats(self):
        steps = render_search({"as_phases": 4, "as_search_clients": [1], "as_time_periods": [1800]})
        assert all(s["time-period"] == 1800 for s in steps)

    def test_single_element_clients_repeats(self):
        steps = render_search({"as_phases": 4, "as_search_clients": [8]})
        assert all(s["clients"] == 8 for s in steps)

    def test_target_throughput_applied_when_positive(self):
        steps = render_search(
            {
                "as_phases": 4,
                "as_search_clients": [1],
                "as_search_target_throughputs": [500, 2500, 500, 2500],
            }
        )
        assert all("target-throughput" in s for s in steps)
        # phase 0 → 500, phase 1 → 2500 (each phase produces 2 steps)
        assert steps[0]["target-throughput"] == 500
        assert steps[2]["target-throughput"] == 2500

    def test_single_element_throughput_repeats(self):
        steps = render_search(
            {
                "as_phases": 4,
                "as_search_clients": [1],
                "as_search_target_throughputs": [1000],
            }
        )
        assert all(s.get("target-throughput") == 1000 for s in steps)

    def test_minimal_multi_phase_override(self):
        steps = render_search(
            {
                "as_phases": 4,
                "as_search_clients": [1],
                "as_search_target_throughputs": [500, 2500, 500, 2500],
            }
        )
        assert len(steps) == 8
        assert all(s["warmup-time-period"] >= 1 for s in steps)


# --- ingest-search-autoscale-schedule.json ---

INGEST_HEADER_STEPS = 4  # delete-index, create-index, check-cluster-health, initial-ingest


def parallel_steps(items):
    return [item for item in items if "parallel" in item]


def all_tasks(items):
    return [task for item in parallel_steps(items) for task in item["parallel"]["tasks"]]


class TestIngestSearchAutoscaleSchedule:
    def test_default_params_five_phases(self):
        items = render_ingest_search()
        assert len(items) == INGEST_HEADER_STEPS + 5

    def test_default_single_element_ingest_clients_repeats(self):
        # Template default as_ingest_clients=[1] applies to all 5 phases
        items = render_ingest_search()
        ingest_tasks = [t for t in all_tasks(items) if "bulk" in t["operation"]["operation-type"]]
        assert all(t["clients"] == 1 for t in ingest_tasks)

    def test_phase_count_driven_by_as_phases(self):
        items = render_ingest_search({"as_phases": 4, "as_search_clients": [1]})
        assert len(parallel_steps(items)) == 4

    def test_task_warmup_zero_clamped_to_one(self):
        items = render_ingest_search({"as_phases": 3, "as_warmup_time_periods": [0], "as_search_clients": [1]})
        for task in all_tasks(items):
            assert task["warmup-time-period"] >= 1

    def test_task_warmup_positive_value_preserved(self):
        items = render_ingest_search({"as_phases": 4, "as_warmup_time_periods": [30, 0, 0, 0], "as_search_clients": [1]})
        first_phase_tasks = parallel_steps(items)[0]["parallel"]["tasks"]
        assert all(t["warmup-time-period"] == 30 for t in first_phase_tasks)
        for task in all_tasks(items)[len(first_phase_tasks) :]:
            assert task["warmup-time-period"] == 1

    def test_single_element_time_periods_repeats(self):
        items = render_ingest_search({"as_phases": 4, "as_search_clients": [1], "as_time_periods": [900]})
        for task in all_tasks(items):
            assert task["time-period"] == 900

    def test_single_element_ingest_clients_repeats(self):
        items = render_ingest_search({"as_phases": 4, "as_search_clients": [1], "as_ingest_clients": [4]})
        ingest_tasks = [t for t in all_tasks(items) if "bulk" in t["operation"]["operation-type"]]
        assert all(t["clients"] == 4 for t in ingest_tasks)

    def test_single_element_search_clients_repeats(self):
        items = render_ingest_search({"as_phases": 4, "as_search_clients": [8]})
        search_tasks = [t for t in all_tasks(items) if t["operation"]["operation-type"] == "search"]
        assert all(t["clients"] == 8 for t in search_tasks)

    def test_search_target_throughput_applied_when_positive(self):
        items = render_ingest_search(
            {
                "as_phases": 2,
                "as_search_clients": [1],
                "as_search_target_throughputs": [500, 2500],
            }
        )
        search_tasks = [t for t in all_tasks(items) if t["operation"]["operation-type"] == "search"]
        assert all("target-throughput" in t for t in search_tasks)
        assert search_tasks[0]["target-throughput"] == 500
        assert search_tasks[1]["target-throughput"] == 2500

    def test_ingest_target_throughput_applied_when_positive(self):
        items = render_ingest_search(
            {
                "as_phases": 2,
                "as_search_clients": [1],
                "as_ingest_target_throughputs": [200, 400],
            }
        )
        ingest_tasks = [t for t in all_tasks(items) if "bulk" in t["operation"]["operation-type"]]
        assert all("target-throughput" in t for t in ingest_tasks)
        assert ingest_tasks[0]["target-throughput"] == 200
        assert ingest_tasks[1]["target-throughput"] == 400


# --- ingest-autoscale-schedule.json ---

INGEST_ONLY_HEADER_STEPS = 4  # delete-index, create-index, check-cluster-health, initial-ingest


def ingest_phase_steps(items):
    return [
        item
        for item in items
        if isinstance(item.get("operation"), dict)
        and item["operation"].get("operation-type") == "bulk"
        and "warmup-time-period" in item  # excludes the initial-ingest step
    ]


class TestIngestAutoscaleSchedule:
    def test_default_params_five_phases(self):
        items = render_ingest()
        assert len(ingest_phase_steps(items)) == 5

    def test_default_single_element_time_period_repeats(self):
        # Template default as_time_periods=[1800] applies to all 5 phases
        items = render_ingest()
        assert all(s["time-period"] == 1800 for s in ingest_phase_steps(items))

    def test_default_single_element_throughput_is_unlimited(self):
        # Template default as_ingest_target_throughputs=[-1] means no throttle
        items = render_ingest()
        assert all("target-throughput" not in s for s in ingest_phase_steps(items))

    def test_phase_count_driven_by_as_phases(self):
        items = render_ingest({"as_phases": 4, "as_ingest_clients": [1]})
        assert len(ingest_phase_steps(items)) == 4

    def test_warmup_zero_clamped_to_one(self):
        items = render_ingest({"as_phases": 3, "as_warmup_time_periods": [0], "as_ingest_clients": [1]})
        for step in ingest_phase_steps(items):
            assert step["warmup-time-period"] >= 1

    def test_warmup_positive_value_preserved(self):
        items = render_ingest({"as_phases": 4, "as_warmup_time_periods": [30, 0, 0, 0], "as_ingest_clients": [1]})
        steps = ingest_phase_steps(items)
        assert steps[0]["warmup-time-period"] == 30
        assert all(s["warmup-time-period"] == 1 for s in steps[1:])

    def test_single_element_clients_repeats(self):
        items = render_ingest({"as_phases": 4, "as_ingest_clients": [4]})
        assert all(s["clients"] == 4 for s in ingest_phase_steps(items))

    def test_single_element_time_periods_repeats(self):
        items = render_ingest({"as_phases": 4, "as_ingest_clients": [1], "as_time_periods": [900]})
        assert all(s["time-period"] == 900 for s in ingest_phase_steps(items))

    def test_target_throughput_applied_when_positive(self):
        items = render_ingest({"as_phases": 2, "as_ingest_clients": [1], "as_ingest_target_throughputs": [200, 400]})
        steps = ingest_phase_steps(items)
        assert all("target-throughput" in s for s in steps)
        assert steps[0]["target-throughput"] == 200
        assert steps[1]["target-throughput"] == 400

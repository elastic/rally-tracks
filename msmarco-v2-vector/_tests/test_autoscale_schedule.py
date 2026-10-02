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

import importlib.util
import json
import pathlib
import types

import jinja2
import pytest

COMMON_DIR = pathlib.Path(__file__).parents[1] / "challenges" / "common"

# Import the track module under a unique name to avoid colliding with other
# tracks' track.py modules when the whole repo's tests are collected together.
_TRACK_PY = pathlib.Path(__file__).parents[1] / "track.py"
_spec = importlib.util.spec_from_file_location("msmarco_v2_vector_track", _TRACK_PY)
track_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(track_module)


def fake_track(index_name="msmarco-v2"):
    return types.SimpleNamespace(indices=[types.SimpleNamespace(name=index_name)])


class FakeEs:
    def __init__(self):
        self.requests = []

    async def perform_request(self, method, path, body=None, **kwargs):
        self.requests.append({"method": method, "path": path, "body": body})
        return {"acknowledged": True}


class FlakyEs:
    # Raises the queued exceptions on successive calls (None = succeed), so tests
    # can drive the Retry wrapper's retry/no-retry behavior.
    def __init__(self, outcomes):
        self._outcomes = list(outcomes)
        self.requests = []

    async def perform_request(self, method, path, body=None, **kwargs):
        if self._outcomes:
            outcome = self._outcomes.pop(0)
            if outcome is not None:
                raise outcome
        self.requests.append({"method": method, "path": path, "body": body})
        return {"acknowledged": True}


class FakeRegistry:
    def __init__(self):
        self.param_sources = {}
        self.runners = {}

    def register_param_source(self, name, cls):
        self.param_sources[name] = cls

    def register_runner(self, name, instance, **kwargs):
        self.runners[name] = instance


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

    def test_as_warmup_time_periods_drives_phases_when_as_phases_absent(self):
        # backward compat: existing configs that pass as_warmup_time_periods without as_phases
        steps = render_search({"as_warmup_time_periods": [1200], "as_search_clients": [1000], "as_search_target_throughputs": [1000]})
        assert len(steps) == 2  # 1 phase × 2 query sizes

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

    def test_as_warmup_time_periods_drives_phases_when_as_phases_absent(self):
        # backward compat: as_warmup_time_periods length sets phase count when as_phases is not given
        items = render_ingest_search({"as_warmup_time_periods": [1200], "as_search_clients": [1000]})
        assert len(parallel_steps(items)) == 1

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

    def test_as_warmup_time_periods_drives_phases_when_as_phases_absent(self):
        # backward compat: as_warmup_time_periods length sets phase count when as_phases is not given
        items = render_ingest({"as_warmup_time_periods": [1200], "as_ingest_clients": [1]})
        assert len(ingest_phase_steps(items)) == 1

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


# --- per-phase ES settings: SettingsParamSource (key routing / validation) ---


class TestSettingsParamSource:
    def test_routes_index_settings(self):
        ps = track_module.SettingsParamSource(fake_track(), {"settings": {"index.number_of_replicas": 1, "index.refresh_interval": "5s"}})
        p = ps.params()
        assert p["index"] == "msmarco-v2"
        assert p["index_settings"] == {"number_of_replicas": 1, "refresh_interval": "5s"}
        assert p["cluster_body"] == {}

    def test_routes_cluster_settings_as_persistent(self):
        # non-index keys go to the cluster settings API, always wrapped in persistent
        ps = track_module.SettingsParamSource(
            fake_track(),
            {
                "settings": {
                    "indices.recovery.max_bytes_per_sec": "200mb",
                    "cluster.routing.allocation.enable": "all",
                }
            },
        )
        p = ps.params()
        assert p["index_settings"] == {}
        assert p["cluster_body"] == {
            "persistent": {
                "indices.recovery.max_bytes_per_sec": "200mb",
                "cluster.routing.allocation.enable": "all",
            }
        }

    def test_mixed_index_and_cluster_keys(self):
        ps = track_module.SettingsParamSource(
            fake_track(), {"settings": {"index.number_of_replicas": 2, "indices.recovery.max_bytes_per_sec": "200mb"}}
        )
        p = ps.params()
        assert p["index_settings"] == {"number_of_replicas": 2}
        assert p["cluster_body"] == {"persistent": {"indices.recovery.max_bytes_per_sec": "200mb"}}

    def test_non_dict_settings_raises(self):
        # a non-object as_settings entry fails fast with a clear message, not AttributeError
        with pytest.raises(ValueError, match="must be an object"):
            track_module.SettingsParamSource(fake_track(), {"settings": "refresh_interval=5s"})

    def test_indices_prefix_routed_to_cluster_not_index(self):
        # `indices.*` is a cluster namespace and must NOT collide with the `index.` index
        # prefix; it routes to the cluster settings API, not the index one
        ps = track_module.SettingsParamSource(fake_track(), {"settings": {"indices.recovery.max_bytes_per_sec": "200mb"}})
        p = ps.params()
        assert p["index_settings"] == {}
        assert p["cluster_body"] == {"persistent": {"indices.recovery.max_bytes_per_sec": "200mb"}}

    def test_bare_index_setting_routed_to_cluster(self):
        # documented footgun: an index setting written WITHOUT the canonical `index.` prefix
        # is treated as a cluster setting (and would then be rejected by Elasticsearch)
        ps = track_module.SettingsParamSource(fake_track(), {"settings": {"number_of_replicas": 1}})
        p = ps.params()
        assert p["index_settings"] == {}
        assert p["cluster_body"] == {"persistent": {"number_of_replicas": 1}}

    def test_index_override(self):
        ps = track_module.SettingsParamSource(fake_track(), {"index": "other-index", "settings": {"index.x": 1}})
        assert ps.params()["index"] == "other-index"

    def test_empty_settings(self):
        ps = track_module.SettingsParamSource(fake_track(), {})
        p = ps.params()
        assert p["index_settings"] == {}
        assert p["cluster_body"] == {}


# --- per-phase ES settings: ConfigureSettingsRunner (request issuing) ---


class TestConfigureSettingsRunner:
    @pytest.mark.asyncio
    async def test_issues_index_and_cluster_requests(self):
        es = FakeEs()
        await track_module.ConfigureSettingsRunner()(
            es,
            {
                "index": "msmarco-v2",
                "index_settings": {"number_of_replicas": 1},
                "cluster_body": {"persistent": {"foo": "bar"}},
            },
        )
        assert es.requests == [
            {"method": "PUT", "path": "/msmarco-v2/_settings", "body": {"index": {"number_of_replicas": 1}}},
            {"method": "PUT", "path": "/_cluster/settings", "body": {"persistent": {"foo": "bar"}}},
        ]

    @pytest.mark.asyncio
    async def test_no_requests_when_empty(self):
        es = FakeEs()
        await track_module.ConfigureSettingsRunner()(es, {"index": "msmarco-v2", "index_settings": {}, "cluster_body": {}})
        assert es.requests == []

    @pytest.mark.asyncio
    async def test_only_index_request(self):
        es = FakeEs()
        await track_module.ConfigureSettingsRunner()(es, {"index": "i", "index_settings": {"refresh_interval": "-1"}, "cluster_body": {}})
        assert len(es.requests) == 1
        assert es.requests[0]["path"] == "/i/_settings"

    @pytest.mark.asyncio
    async def test_only_cluster_request(self):
        es = FakeEs()
        await track_module.ConfigureSettingsRunner()(
            es, {"index": "i", "index_settings": {}, "cluster_body": {"persistent": {"foo": "bar"}}}
        )
        assert es.requests == [{"method": "PUT", "path": "/_cluster/settings", "body": {"persistent": {"foo": "bar"}}}]


# --- per-phase ES settings: SettingsParamSource -> ConfigureSettingsRunner end to end ---


class TestSettingsParamSourceToRunner:
    @pytest.mark.asyncio
    async def test_param_source_output_feeds_runner(self):
        # guards against key-name drift between the two halves of the contract
        ps = track_module.SettingsParamSource(
            fake_track(),
            {
                "settings": {
                    "index.number_of_replicas": 1,
                    "indices.recovery.max_bytes_per_sec": "200mb",
                }
            },
        )
        es = FakeEs()
        await track_module.ConfigureSettingsRunner()(es, ps.params())
        assert es.requests == [
            {"method": "PUT", "path": "/msmarco-v2/_settings", "body": {"index": {"number_of_replicas": 1}}},
            {
                "method": "PUT",
                "path": "/_cluster/settings",
                "body": {"persistent": {"indices.recovery.max_bytes_per_sec": "200mb"}},
            },
        ]

    @pytest.mark.asyncio
    async def test_empty_param_source_issues_no_requests(self):
        ps = track_module.SettingsParamSource(fake_track(), {})
        es = FakeEs()
        await track_module.ConfigureSettingsRunner()(es, ps.params())
        assert es.requests == []


# --- per-phase ES settings: template rendering across all three challenges ---


def configure_settings_steps(items):
    return [s for s in items if isinstance(s.get("name"), str) and s["name"].startswith("configure-settings")]


class TestPerPhaseSettings:
    def test_search_no_settings_step_by_default(self):
        assert configure_settings_steps(render_search()) == []

    def test_ingest_no_settings_step_by_default(self):
        assert configure_settings_steps(render_ingest()) == []

    def test_ingest_search_no_settings_step_by_default(self):
        assert configure_settings_steps(render_ingest_search()) == []

    def test_search_emits_settings_step(self):
        steps = render_search({"as_phases": 1, "as_search_clients": [1], "as_settings": [{"index.number_of_replicas": 1}]})
        cs = configure_settings_steps(steps)
        assert len(cs) == 1
        op = cs[0]["operation"]
        assert op["operation-type"] == "configure-settings"
        assert op["param-source"] == "settings-param-source"
        assert op["settings"] == {"index.number_of_replicas": 1}
        assert op["retries"] == 3  # default transient-retry count

    def test_search_settings_retries_override(self):
        steps = render_search(
            {"as_phases": 1, "as_search_clients": [1], "as_settings": [{"index.number_of_replicas": 1}], "as_settings_retries": 5}
        )
        assert configure_settings_steps(steps)[0]["operation"]["retries"] == 5

    def test_search_negative_retries_clamped_to_zero(self):
        # negative retries would make Retry skip the runner entirely (range(0)); clamp to 0
        steps = render_search(
            {"as_phases": 1, "as_search_clients": [1], "as_settings": [{"index.number_of_replicas": 1}], "as_settings_retries": -1}
        )
        assert configure_settings_steps(steps)[0]["operation"]["retries"] == 0

    def test_search_settings_step_precedes_search(self):
        steps = render_search({"as_phases": 1, "as_search_clients": [1], "as_settings": [{"index.number_of_replicas": 1}]})
        assert steps[0]["name"].startswith("configure-settings")
        assert steps[1]["name"].startswith("search-")

    def test_search_settings_only_on_nonempty_phase(self):
        # phase 0 has settings, phase 1 is empty -> only one settings step
        steps = render_search({"as_phases": 2, "as_search_clients": [1], "as_settings": [{"index.number_of_replicas": 1}, {}]})
        assert len(configure_settings_steps(steps)) == 1

    def test_search_null_phase_skips_settings(self):
        # null is equivalent to {} for opting a phase out of settings
        steps = render_search({"as_phases": 2, "as_search_clients": [1], "as_settings": [{"index.number_of_replicas": 1}, None]})
        assert len(configure_settings_steps(steps)) == 1

    def test_search_all_null_settings_emits_nothing(self):
        steps = render_search({"as_phases": 2, "as_search_clients": [1], "as_settings": [None]})
        assert configure_settings_steps(steps) == []

    def test_search_single_element_settings_repeats(self):
        steps = render_search({"as_phases": 3, "as_search_clients": [1], "as_settings": [{"index.refresh_interval": "5s"}]})
        assert len(configure_settings_steps(steps)) == 3

    def test_search_multi_element_settings_assigned_per_phase(self):
        # as_phases (4) > len(as_settings) (2): objects are assigned per phase via modulo (A,B,A,B)
        a = {"index.number_of_replicas": 0}
        b = {"index.number_of_replicas": 1}
        steps = render_search({"as_phases": 4, "as_search_clients": [1], "as_settings": [a, b]})
        payloads = [s["operation"]["settings"] for s in configure_settings_steps(steps)]
        assert payloads == [a, b, a, b]

    def test_search_more_settings_than_phases_ignores_extra(self):
        # as_phases (2) < len(as_settings) (3): only the first two objects are used
        a = {"index.number_of_replicas": 0}
        b = {"index.number_of_replicas": 1}
        c = {"index.number_of_replicas": 2}
        steps = render_search({"as_phases": 2, "as_search_clients": [1], "as_settings": [a, b, c]})
        payloads = [s["operation"]["settings"] for s in configure_settings_steps(steps)]
        assert payloads == [a, b]

    def test_ingest_emits_settings_step(self):
        items = render_ingest({"as_phases": 1, "as_ingest_clients": [1], "as_settings": [{"index.refresh_interval": "-1"}]})
        cs = configure_settings_steps(items)
        assert len(cs) == 1
        assert cs[0]["operation"]["settings"] == {"index.refresh_interval": "-1"}

    def test_ingest_settings_step_precedes_bulk(self):
        items = render_ingest({"as_phases": 1, "as_ingest_clients": [1], "as_settings": [{"index.refresh_interval": "-1"}]})
        cs_idx = next(i for i, s in enumerate(items) if isinstance(s.get("name"), str) and s["name"].startswith("configure-settings"))
        bulk_idx = next(
            i
            for i, s in enumerate(items)
            if isinstance(s.get("operation"), dict) and s["operation"].get("operation-type") == "bulk" and "warmup-time-period" in s
        )
        assert cs_idx < bulk_idx

    def test_ingest_search_emits_settings_step_before_parallel(self):
        items = render_ingest_search({"as_phases": 1, "as_search_clients": [1], "as_settings": [{"index.number_of_replicas": 2}]})
        cs = configure_settings_steps(items)
        assert len(cs) == 1
        cs_idx = next(i for i, s in enumerate(items) if isinstance(s.get("name"), str) and s["name"].startswith("configure-settings"))
        par_idx = next(i for i, s in enumerate(items) if "parallel" in s)
        assert cs_idx < par_idx


# --- per-phase ES settings: registration ---


class TestRegistration:
    def test_configure_settings_runner_wrapped_in_retry(self):
        reg = FakeRegistry()
        track_module.register(reg)
        r = reg.runners["configure-settings"]
        # wrapping in Retry is what enables transient-failure retries on the settings request
        assert isinstance(r, track_module.runner.Retry)
        assert isinstance(r.delegate, track_module.ConfigureSettingsRunner)

    def test_settings_param_source_registered(self):
        reg = FakeRegistry()
        track_module.register(reg)
        assert reg.param_sources["settings-param-source"] is track_module.SettingsParamSource

    @pytest.mark.asyncio
    async def test_retry_wrapped_runner_executes_via_async_with(self):
        # Rally's driver enters every runner via `async with`; Retry delegates __aenter__
        # to the wrapped runner. A delegate lacking the context-manager protocol raises
        # AttributeError here, so this guards the wiring the unit-level runner tests miss.
        es = FakeEs()
        wrapped = track_module.runner.Retry(track_module.ConfigureSettingsRunner())
        async with wrapped as r:
            await r(es, {"index": "i", "index_settings": {"number_of_replicas": 1}, "cluster_body": {}, "retries": 3})
        assert es.requests == [{"method": "PUT", "path": "/i/_settings", "body": {"index": {"number_of_replicas": 1}}}]

    def test_param_source_echoes_retries(self):
        # the param-source must pass operation-level retry knobs through, otherwise
        # the Retry wrapper never sees them and silently never retries
        ps = track_module.SettingsParamSource(fake_track(), {"settings": {"index.x": 1}, "retries": 7})
        assert ps.params()["retries"] == 7

    @pytest.mark.asyncio
    async def test_retry_retries_transient_connection_error(self):
        import elasticsearch

        # build params via the param-source so this exercises the REAL flow: `retries`
        # must survive the param-source for Retry to act on it. Fail once with a
        # transient connection error, then succeed -> Retry re-runs the op.
        ps = track_module.SettingsParamSource(
            fake_track(), {"settings": {"index.number_of_replicas": 1}, "retries": 3, "retry-wait-period": 0}
        )
        es = FlakyEs([elasticsearch.ConnectionError("boom"), None])
        wrapped = track_module.runner.Retry(track_module.ConfigureSettingsRunner())
        async with wrapped as r:
            await r(es, ps.params())
        assert len(es.requests) == 1

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
_spec = importlib.util.spec_from_file_location("wikipedia_track", _TRACK_PY)
track_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(track_module)


def fake_track(index_name="wikipedia"):
    return types.SimpleNamespace(indices=[types.SimpleNamespace(name=index_name)])


class FakeEs:
    def __init__(self):
        self.requests = []

    async def perform_request(self, method, path, body=None, **kwargs):
        self.requests.append({"method": method, "path": path, "body": body})
        return {"acknowledged": True}


class FlakyEs:
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


def single_phase(**extra):
    # Wikipedia autoscale phase count is driven by array lengths (not as_phases).
    base = {
        "as_warmup_time_periods": [60],
        "as_time_periods": [120],
        "as_search_clients": [1],
        "as_search_target_throughputs": [-1],
        "as_ingest_clients": [1],
        "as_ingest_target_throughputs": [-1],
    }
    base.update(extra)
    return base


def render_search(params=None):
    return render("search-autoscale-schedule.json", params or {})


def render_ingest_search(params=None):
    return render("ingest-search-autoscale-schedule.json", params or {})


def render_ingest(params=None):
    return render("ingest-autoscale-schedule.json", params or {})


def configure_settings_steps(items):
    return [s for s in items if isinstance(s.get("name"), str) and s["name"].startswith("configure-settings")]


# --- per-phase ES settings: SettingsParamSource ---


class TestSettingsParamSource:
    def test_routes_index_settings(self):
        ps = track_module.SettingsParamSource(fake_track(), {"settings": {"index.number_of_replicas": 1, "index.refresh_interval": "5s"}})
        p = ps.params()
        assert p["index"] == "wikipedia"
        assert p["index_settings"] == {"number_of_replicas": 1, "refresh_interval": "5s"}
        assert p["cluster_body"] == {}

    def test_routes_cluster_settings_as_persistent(self):
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
        with pytest.raises(ValueError, match="must be an object"):
            track_module.SettingsParamSource(fake_track(), {"settings": "refresh_interval=5s"})

    def test_indices_prefix_routed_to_cluster_not_index(self):
        ps = track_module.SettingsParamSource(fake_track(), {"settings": {"indices.recovery.max_bytes_per_sec": "200mb"}})
        p = ps.params()
        assert p["index_settings"] == {}
        assert p["cluster_body"] == {"persistent": {"indices.recovery.max_bytes_per_sec": "200mb"}}

    def test_bare_index_setting_routed_to_cluster(self):
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


# --- ConfigureSettingsRunner ---


class TestConfigureSettingsRunner:
    @pytest.mark.asyncio
    async def test_issues_index_and_cluster_requests(self):
        es = FakeEs()
        await track_module.ConfigureSettingsRunner()(
            es,
            {
                "index": "wikipedia",
                "index_settings": {"number_of_replicas": 1},
                "cluster_body": {"persistent": {"foo": "bar"}},
            },
        )
        assert es.requests == [
            {"method": "PUT", "path": "/wikipedia/_settings", "body": {"index": {"number_of_replicas": 1}}},
            {"method": "PUT", "path": "/_cluster/settings", "body": {"persistent": {"foo": "bar"}}},
        ]

    @pytest.mark.asyncio
    async def test_no_requests_when_empty(self):
        es = FakeEs()
        await track_module.ConfigureSettingsRunner()(es, {"index": "wikipedia", "index_settings": {}, "cluster_body": {}})
        assert es.requests == []

    @pytest.mark.asyncio
    async def test_param_source_output_feeds_runner(self):
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
            {"method": "PUT", "path": "/wikipedia/_settings", "body": {"index": {"number_of_replicas": 1}}},
            {"method": "PUT", "path": "/_cluster/settings", "body": {"persistent": {"indices.recovery.max_bytes_per_sec": "200mb"}}},
        ]

    @pytest.mark.asyncio
    async def test_empty_param_source_issues_no_requests(self):
        ps = track_module.SettingsParamSource(fake_track(), {})
        es = FakeEs()
        await track_module.ConfigureSettingsRunner()(es, ps.params())
        assert es.requests == []


# --- template rendering ---


class TestPerPhaseSettings:
    def test_search_no_settings_step_by_default(self):
        assert configure_settings_steps(render_search()) == []

    def test_ingest_no_settings_step_by_default(self):
        assert configure_settings_steps(render_ingest()) == []

    def test_ingest_search_no_settings_step_by_default(self):
        assert configure_settings_steps(render_ingest_search()) == []

    def test_search_emits_settings_step(self):
        steps = render_search(single_phase(as_settings=[{"index.number_of_replicas": 1}]))
        cs = configure_settings_steps(steps)
        assert len(cs) == 1
        op = cs[0]["operation"]
        assert op["operation-type"] == "configure-settings"
        assert op["param-source"] == "settings-param-source"
        assert op["settings"] == {"index.number_of_replicas": 1}
        assert op["retries"] == 3

    def test_search_settings_retries_override(self):
        steps = render_search(single_phase(as_settings=[{"index.number_of_replicas": 1}], as_settings_retries=5))
        assert configure_settings_steps(steps)[0]["operation"]["retries"] == 5

    def test_search_negative_retries_clamped_to_zero(self):
        steps = render_search(single_phase(as_settings=[{"index.number_of_replicas": 1}], as_settings_retries=-1))
        assert configure_settings_steps(steps)[0]["operation"]["retries"] == 0

    def test_search_settings_step_precedes_search(self):
        steps = render_search(single_phase(as_settings=[{"index.number_of_replicas": 1}]))
        cs_idx = next(i for i, s in enumerate(steps) if isinstance(s.get("name"), str) and s["name"].startswith("configure-settings"))
        search_idx = next(i for i, s in enumerate(steps) if isinstance(s.get("name"), str) and s["name"].startswith("search-"))
        assert cs_idx < search_idx

    def test_search_settings_only_on_nonempty_phase(self):
        steps = render_search(
            {
                "as_warmup_time_periods": [60, 60],
                "as_time_periods": [120, 120],
                "as_search_clients": [1, 1],
                "as_search_target_throughputs": [-1, -1],
                "as_settings": [{"index.number_of_replicas": 1}, {}],
            }
        )
        assert len(configure_settings_steps(steps)) == 1

    def test_search_null_phase_skips_settings(self):
        steps = render_search(
            {
                "as_warmup_time_periods": [60, 60],
                "as_time_periods": [120, 120],
                "as_search_clients": [1, 1],
                "as_search_target_throughputs": [-1, -1],
                "as_settings": [{"index.number_of_replicas": 1}, None],
            }
        )
        assert len(configure_settings_steps(steps)) == 1

    def test_search_all_null_settings_emits_nothing(self):
        steps = render_search(
            {
                "as_warmup_time_periods": [60, 60],
                "as_time_periods": [120, 120],
                "as_search_clients": [1, 1],
                "as_search_target_throughputs": [-1, -1],
                "as_settings": [None],
            }
        )
        assert configure_settings_steps(steps) == []

    def test_search_single_element_settings_repeats(self):
        steps = render_search(
            {
                "as_warmup_time_periods": [60, 60, 60],
                "as_time_periods": [120, 120, 120],
                "as_search_clients": [1, 1, 1],
                "as_search_target_throughputs": [-1, -1, -1],
                "as_settings": [{"index.refresh_interval": "5s"}],
            }
        )
        assert len(configure_settings_steps(steps)) == 3

    def test_search_multi_element_settings_assigned_per_phase(self):
        a = {"index.number_of_replicas": 0}
        b = {"index.number_of_replicas": 1}
        steps = render_search(
            {
                "as_warmup_time_periods": [60, 60, 60, 60],
                "as_time_periods": [120, 120, 120, 120],
                "as_search_clients": [1, 1, 1, 1],
                "as_search_target_throughputs": [-1, -1, -1, -1],
                "as_settings": [a, b],
            }
        )
        payloads = [s["operation"]["settings"] for s in configure_settings_steps(steps)]
        assert payloads == [a, b, a, b]

    def test_search_more_settings_than_phases_ignores_extra(self):
        a = {"index.number_of_replicas": 0}
        b = {"index.number_of_replicas": 1}
        c = {"index.number_of_replicas": 2}
        steps = render_search(
            {
                "as_warmup_time_periods": [60, 60],
                "as_time_periods": [120, 120],
                "as_search_clients": [1, 1],
                "as_search_target_throughputs": [-1, -1],
                "as_settings": [a, b, c],
            }
        )
        payloads = [s["operation"]["settings"] for s in configure_settings_steps(steps)]
        assert payloads == [a, b]

    def test_ingest_emits_settings_step(self):
        items = render_ingest(single_phase(as_settings=[{"index.refresh_interval": "-1"}]))
        cs = configure_settings_steps(items)
        assert len(cs) == 1
        assert cs[0]["operation"]["settings"] == {"index.refresh_interval": "-1"}

    def test_ingest_settings_step_precedes_bulk(self):
        items = render_ingest(single_phase(as_settings=[{"index.refresh_interval": "-1"}]))
        cs_idx = next(i for i, s in enumerate(items) if isinstance(s.get("name"), str) and s["name"].startswith("configure-settings"))
        bulk_idx = next(
            i
            for i, s in enumerate(items)
            if isinstance(s.get("operation"), dict) and s["operation"].get("operation-type") == "bulk" and "warmup-time-period" in s
        )
        assert cs_idx < bulk_idx

    def test_ingest_settings_modulo_with_ingest_client_driven_phases(self):
        # ingest-autoscale phase count is driven by as_ingest_clients, not warmup length
        a = {"index.refresh_interval": "-1"}
        b = {"index.refresh_interval": "5s"}
        items = render_ingest(
            {
                "as_ingest_clients": [1, 2, 4],
                "as_warmup_time_periods": [60, 60, 60],
                "as_time_periods": [120, 120, 120],
                "as_ingest_target_throughputs": [-1, -1, -1],
                "as_settings": [a, b],
            }
        )
        payloads = [s["operation"]["settings"] for s in configure_settings_steps(items)]
        assert payloads == [a, b, a]

    def test_ingest_search_emits_settings_step_before_parallel(self):
        items = render_ingest_search(single_phase(as_settings=[{"index.number_of_replicas": 2}]))
        assert len(configure_settings_steps(items)) == 1
        cs_idx = next(i for i, s in enumerate(items) if isinstance(s.get("name"), str) and s["name"].startswith("configure-settings"))
        par_idx = next(i for i, s in enumerate(items) if "parallel" in s)
        assert cs_idx < par_idx


# --- registration ---


class TestRegistration:
    def test_configure_settings_runner_wrapped_in_retry(self):
        reg = FakeRegistry()
        track_module.register(reg)
        r = reg.runners["configure-settings"]
        assert isinstance(r, track_module.runner.Retry)
        assert isinstance(r.delegate, track_module.ConfigureSettingsRunner)

    def test_settings_param_source_registered(self):
        reg = FakeRegistry()
        track_module.register(reg)
        assert reg.param_sources["settings-param-source"] is track_module.SettingsParamSource

    @pytest.mark.asyncio
    async def test_retry_wrapped_runner_executes_via_async_with(self):
        es = FakeEs()
        wrapped = track_module.runner.Retry(track_module.ConfigureSettingsRunner())
        async with wrapped as r:
            await r(es, {"index": "i", "index_settings": {"number_of_replicas": 1}, "cluster_body": {}, "retries": 3})
        assert es.requests == [{"method": "PUT", "path": "/i/_settings", "body": {"index": {"number_of_replicas": 1}}}]

    def test_param_source_echoes_retries(self):
        ps = track_module.SettingsParamSource(fake_track(), {"settings": {"index.x": 1}, "retries": 7})
        assert ps.params()["retries"] == 7

    @pytest.mark.asyncio
    async def test_retry_retries_transient_connection_error(self):
        import elasticsearch

        ps = track_module.SettingsParamSource(
            fake_track(), {"settings": {"index.number_of_replicas": 1}, "retries": 3, "retry-wait-period": 0}
        )
        es = FlakyEs([elasticsearch.ConnectionError("boom"), None])
        wrapped = track_module.runner.Retry(track_module.ConfigureSettingsRunner())
        async with wrapped as r:
            await r(es, ps.params())
        assert len(es.requests) == 1

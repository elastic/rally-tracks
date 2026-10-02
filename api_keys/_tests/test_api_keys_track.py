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

import collections
import importlib.util
import json
import pathlib
import stat
import types

import jinja2
import pytest

TRACK_DIR = pathlib.Path(__file__).parents[1]

# Import the track module under a unique name to avoid colliding with other
# tracks' track.py modules when the whole repo's tests are collected together.
_spec = importlib.util.spec_from_file_location("api_keys_track", TRACK_DIR / "track.py")
track_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(track_module)

# (num_api_keys, create_clients, create_batch_size); the last shape has more creation clients than API keys
CREATE_SHAPES = [(10000, 8, 100), (200, 2, 25), (100001, 7, 33), (4, 8, 100)]


def render(template_name, **track_params):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(TRACK_DIR)))
    return env.get_template(template_name).render(**track_params)


def render_operations(**track_params):
    return {op["name"]: op for op in json.loads(f"[{render('operations/default.json', **track_params)}]")}


def render_schedule(**track_params):
    return json.loads(render("challenges/default.json", **track_params))["schedule"]


def scheduled_task(operation, **track_params):
    return next(task for task in render_schedule(**track_params) if task["operation"] == operation)


def drain(param_source):
    params = []
    try:
        while True:
            params.append(param_source.params())
    except StopIteration:
        return params


def create_partitions(directory, num_api_keys, create_clients, create_batch_size):
    param_source = track_module.ApiKeyCreateParamSource(
        None, {"api_keys_dir": str(directory), "num_api_keys": num_api_keys, "create_batch_size": create_batch_size}
    )
    return [param_source.partition(i, create_clients) for i in range(create_clients)]


def write_key_files(directory, num_api_keys, create_clients):
    for client in range(create_clients):
        with open(track_module.key_file(str(directory), client), "w", encoding="utf-8") as f:
            for index in range(client, num_api_keys, create_clients):
                f.write(json.dumps({"index": index, "id": f"id-{index}", "encoded": f"encoded-{index}"}) + "\n")


def read_key_file(directory, client):
    with open(track_module.key_file(str(directory), client), encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def authenticate_partitions(directory, clients, create_clients, **params):
    param_source = track_module.ApiKeyAuthenticateParamSource(
        None, {"api_keys_dir": str(directory), "create_clients": create_clients, **params}
    )
    return [param_source.partition(i, clients) for i in range(clients)]


class FakeSecurity:
    def __init__(self, failing_key_indices=()):
        self.failing_key_indices = set(failing_key_indices)
        self.grants = []

    async def grant_api_key(self, **kwargs):
        self.grants.append(kwargs)
        index = kwargs["api_key"]["metadata"]["key_index"]
        if index in self.failing_key_indices:
            raise RuntimeError(f"grant of API key {index} failed")
        return {"id": f"id-{index}", "encoded": f"encoded-{index}"}


class FakeEs:
    def __init__(self, security):
        self.security = security
        self.options_calls = []

    def options(self, **kwargs):
        self.options_calls.append(kwargs)
        return self


class FakeStatsEs:
    def __init__(self):
        self.ticks = 0
        self.nodes = types.SimpleNamespace(stats=self._nodes_stats)
        self.indices = types.SimpleNamespace(stats=self._indices_stats)

    async def _nodes_stats(self, metric):
        node = {
            "thread_pool": {"security-crypto": {"completed": self.ticks, "rejected": 0, "largest": 4}},
            "process": {"cpu": {"total_in_millis": 10 * self.ticks}},
            "http": {"routes": {"/_security/_authenticate": {"requests": {"count": 100 * self.ticks}}}},
        }
        return {"nodes": {"node-0": node}}

    async def _indices_stats(self, index, metric):
        return {"_all": {"total": {"get": {"total": 2 * self.ticks, "missing_total": 0}}}}


class TestApiKeyCreateParamSource:
    @pytest.mark.parametrize("num_api_keys, create_clients, create_batch_size", CREATE_SHAPES)
    def test_partitions_create_every_api_key_once(self, tmp_path, num_api_keys, create_clients, create_batch_size):
        partitions = create_partitions(tmp_path, num_api_keys, create_clients, create_batch_size)
        indices = [index for partition in partitions for params in drain(partition) for index in params["key_indices"]]
        assert sorted(indices) == list(range(num_api_keys))

    @pytest.mark.parametrize("num_api_keys, create_clients, create_batch_size", CREATE_SHAPES)
    def test_challenge_iterations_cover_largest_partition(self, tmp_path, num_api_keys, create_clients, create_batch_size):
        task = scheduled_task(
            "create-api-keys", num_api_keys=num_api_keys, create_clients=create_clients, create_batch_size=create_batch_size
        )
        partitions = create_partitions(tmp_path, num_api_keys, create_clients, create_batch_size)
        assert task["clients"] == create_clients
        assert task["iterations"] == max(partition.size() for partition in partitions)

    def test_resets_key_file_readable_by_owner_only(self, tmp_path):
        key_file = pathlib.Path(track_module.key_file(str(tmp_path), 0))
        key_file.write_text('{"index": 0}\n')
        key_file.chmod(0o644)
        [partition] = create_partitions(tmp_path, 10, 1, 10)
        partition.params()
        assert key_file.read_text() == ""
        assert stat.S_IMODE(key_file.stat().st_mode) == 0o600

    def test_partition_without_api_keys_resets_its_key_file(self, tmp_path):
        key_file = pathlib.Path(track_module.key_file(str(tmp_path), 1))
        key_file.write_text('{"index": 1}\n')
        partitions = create_partitions(tmp_path, 1, 2, 10)
        assert drain(partitions[1]) == []
        assert key_file.read_text() == ""


class TestPopulation:
    def test_is_deterministic_per_seed(self):
        def population(seed):
            return [track_module.api_key_spec(index, seed, 100, 50, 0.5) for index in range(1000)]

        assert population(42) == population(42)
        assert population(42) != population(43)
        assert track_module.role_descriptor_template(42, 7) == track_module.role_descriptor_template(42, 7)
        assert track_module.role_descriptor_template(42, 7) != track_module.role_descriptor_template(43, 7)

    def test_assigns_role_descriptor_templates_independently_of_owners(self):
        templates_per_owner = collections.defaultdict(set)
        for index in range(10000):
            spec = track_module.api_key_spec(index, 42, 100, 50, 0.5)
            if spec.rd_template is not None:
                templates_per_owner[spec.owner].add(spec.rd_template)
        assert len(templates_per_owner) == 100
        assert all(len(templates) > 1 for templates in templates_per_owner.values())

    @pytest.mark.parametrize("assigned_rd_ratio, assigned", [(0.0, False), (1.0, True)])
    def test_assigned_rd_ratio_bounds(self, assigned_rd_ratio, assigned):
        specs = [track_module.api_key_spec(index, 42, 10, 5, assigned_rd_ratio) for index in range(100)]
        assert all((spec.rd_template is not None) == assigned for spec in specs)


class TestApiKeyAuthenticateParamSource:
    @pytest.mark.parametrize("num_api_keys, clients", [(1003, 8), (200, 2), (5, 8)])
    def test_sweep_authenticates_with_every_api_key_once(self, tmp_path, num_api_keys, clients):
        write_key_files(tmp_path, num_api_keys, create_clients=3)
        partitions = authenticate_partitions(tmp_path, clients, create_clients=3, access_pattern="sweep")
        encoded = [params["encoded_api_key"] for partition in partitions for params in drain(partition)]
        assert sorted(encoded) == sorted(f"encoded-{index}" for index in range(num_api_keys))
        task = scheduled_task("prime-api-key-caches", num_api_keys=num_api_keys, clients=clients)
        assert task["iterations"] == max(partition.size() for partition in partitions)

    def test_request_sequence_is_deterministic_per_seed(self, tmp_path):
        write_key_files(tmp_path, 100, create_clients=2)

        def requests(seed):
            [partition] = authenticate_partitions(tmp_path, 1, create_clients=2, seed=seed, invalid_credentials_ratio=0.1)
            return [partition.params() for _ in range(100)]

        assert requests(42) == requests(42)
        assert requests(42) != requests(43)
        assert any(params["expect_failure"] for params in requests(42))

    def test_hotset_sends_hot_ratio_of_requests_to_hot_fraction_of_api_keys(self, tmp_path):
        write_key_files(tmp_path, 1000, create_clients=1)
        [partition] = authenticate_partitions(tmp_path, 1, create_clients=1, access_pattern="hotset", hot_fraction=0.01, hot_ratio=0.9)
        requests = collections.Counter(partition.params()["encoded_api_key"] for _ in range(10000))
        hot_requests = sum(count for _, count in requests.most_common(10))
        assert hot_requests / 10000 == pytest.approx(0.9, abs=0.02)


class TestRendering:
    def test_api_key_expiration_is_optional(self):
        assert "api_key_expiration" not in render_operations()["create-api-keys"]
        assert render_operations(api_key_expiration="1d")["create-api-keys"]["api_key_expiration"] == "1d"

    def test_kibana_app_privileges_is_a_boolean(self):
        assert render_operations()["create-roles-and-users"]["kibana_app_privileges"] is False
        assert render_operations(kibana_app_privileges=True)["create-roles-and-users"]["kibana_app_privileges"] is True

    def test_target_throughput_is_optional(self):
        assert "target-throughput" not in scheduled_task("authenticate-api-key")
        assert scheduled_task("authenticate-api-key", target_throughput=100)["target-throughput"] == 100

    def test_cleanup_runs_last_when_requested(self):
        assert "cleanup" not in [task["operation"] for task in render_schedule()]
        assert render_schedule(cleanup=True)[-1]["operation"] == "cleanup"


class TestCreateApiKeys:
    @staticmethod
    def params(directory, key_indices):
        return {
            "key_indices": key_indices,
            "key_file": track_module.key_file(str(directory), 0),
            "seed": 42,
            "num_users": 10,
            "num_rd_templates": 5,
            "assigned_rd_ratio": 0.5,
            "api_key_expiration": None,
        }

    @pytest.mark.asyncio
    async def test_grants_api_keys_without_client_retries(self, tmp_path):
        es = FakeEs(FakeSecurity())
        result = await track_module.create_api_keys(es, self.params(tmp_path, [0, 1, 2]))
        assert result == {"weight": 3, "unit": "keys"}
        assert [record["index"] for record in read_key_file(tmp_path, 0)] == [0, 1, 2]
        assert es.options_calls == [{"max_retries": 0}] * 3
        assert [grant["refresh"] for grant in es.security.grants] == ["wait_for"] * 3

    @pytest.mark.asyncio
    async def test_records_created_api_keys_of_a_batch_with_a_failed_grant(self, tmp_path):
        es = FakeEs(FakeSecurity(failing_key_indices={1}))
        with pytest.raises(RuntimeError, match="grant of API key 1 failed"):
            await track_module.create_api_keys(es, self.params(tmp_path, [0, 1, 2]))
        assert [record["index"] for record in read_key_file(tmp_path, 0)] == [0, 2]


class TestCollectSecurityStats:
    @pytest.mark.asyncio
    async def test_reports_counter_deltas_against_a_snapshot_once(self, tmp_path):
        es = FakeStatsEs()
        await track_module.collect_security_stats(es, {"phase": "before", "api_keys_dir": str(tmp_path)})
        es.ticks = 5
        after = await track_module.collect_security_stats(es, {"phase": "after", "api_keys_dir": str(tmp_path)})
        assert after["authenticate_requests_delta"] == 500
        assert after["security_crypto_completed_delta"] == 5
        assert after["security_index_get_total_delta"] == 10
        assert after["cpu_micros_per_authenticate"] == pytest.approx(100.0)
        assert after["security_crypto_tasks_per_authenticate"] == pytest.approx(0.01)
        assert after["security_index_gets_per_authenticate"] == pytest.approx(0.02)
        assert after["window_seconds"] >= 0
        assert "security_crypto_largest_delta" not in after
        assert "nodes_delta" not in after

        again = await track_module.collect_security_stats(es, {"phase": "after", "api_keys_dir": str(tmp_path)})
        assert not any(name.endswith("_delta") for name in again)

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

import ijson
from esrally.driver import runner
from shared import parameter_sources
from shared.parameter_sources.datastream import (
    CreateDataStreamParamSource,
    DataStreamParamSource,
)
from shared.parameter_sources.initial_indices import InitialIndicesParamSource
from shared.parameter_sources.processed import ProcessedCorpusParamSource
from shared.parameter_sources.templates import (
    ComponentTemplateParamSource,
    ComposableTemplateParamSource,
)
from shared.parameter_sources.track_params import TrackParamSource
from shared.parameter_sources.workflow_selector import WorkflowSelectorParamSource
from shared.runners import datastream, snapshot
from shared.runners.bulk import RawBulkIndex
from shared.runners.ilm import create_ilm
from shared.runners.pipelines import create_pipeline
from shared.runners.reindex_data_stream import (
    StartReindexDataStream,
    WaitForReindexDataStream,
)
from shared.runners.remote_cluster import (
    ConfigureCrossClusterReplication,
    ConfigureRemoteClusters,
    MultiClusterWrapper,
)
from shared.runners.slm import create_slm
from shared.runners.update_custom_templates import update_custom_templates
from shared.runners.validate_package_assets import validate_package_assets
from shared.schedulers.indexing import TimestampThrottler
from shared.schedulers.query import WorkflowScheduler
from shared.track_processors import data_generator
from shared.track_processors.track_id_generator import TrackIdGenerator


async def setup_local_remote(es, params):
    response = await es.cluster.state()
    master_node = response["master_node"]
    response = await es.nodes.info()
    ip = response["nodes"][master_node]["transport_address"]
    p_settings = {"cluster.remote.local.seeds": ip}
    response = await es.cluster.put_settings(persistent=p_settings)
    return {"weight": 1, "unit": "ops"}


class EsqlProfileRunner(runner.Runner):
    """
    Runs an ES|QL query using profile: true, and adds the profile information to the result:

    - meta.query.took_ms: Total query time took
    - meta.planning.took_ms: Planning time before query execution, includes parsing, preanalysis, analysis
    - meta.parsing.took_ms: Time it took to parse the ESQL query
    - meta.preanalysis.took_ms: Preanalysis, including field_caps, enrich policies, lookup indices
    - meta.analysis.took_ms: Analysis time before optimizations
    - meta.<plan>.cpu_ms: Total plan CPU time
    - meta.<plan>.took_ms: Total plan took time
    - meta.<plan>.logical_optimization.took_ms: Plan logical optimization took time
    - meta.<plan>.physical_optimization.took_ms: Plan physical optimization took time
    - meta.<plan>.reduction.took_ms: Node reduction plan generation took time
    - meta.<plan>.<operator>.process_ms: Processing time for each operator in the plan
    """

    async def __call__(self, es, params):
        # Extract transport-level parameters (timeouts, headers, etc.)
        params, request_params, transport_params, headers = self._transport_request_params(params)
        es = es.options(**transport_params)

        # Get the ESQL query and params (mandatory parameters)
        query = runner.mandatory(params, "query", self)

        # Build the request body with the query and profile enabled
        body = params.get("body", {})
        body["query"] = query
        body["profile"] = True

        # Add optional filter if provided
        query_filter = params.get("filter")
        if query_filter:
            body["filter"] = query_filter

        # Set headers if not provided (preserves prior behavior)
        if not bool(headers):
            headers = None

        # disable eager response parsing - responses might be huge thus skewing results
        es.return_raw_response()

        result = {}
        try:
            # Execute the ESQL query with profiling using raw request
            response = await es.perform_request(method="POST", path="/_query", headers=headers, body=body, params=request_params)

            # Parse only the profile section from the raw response using ijson
            profile = None
            response.seek(0)
            for item in ijson.items(response, "profile"):
                profile = item
                break

            if not profile:
                result["error"] = "No profile data in response"
                return result

            # Build took_ms entries for each profiled phase
            for phase_name in ["query", "planning", "parsing", "preanalysis", "dependency_resolution", "analysis"]:
                if phase_name in profile:
                    phase_data = profile.get(phase_name, {})
                    if isinstance(phase_data, dict):
                        took_nanos = phase_data.get("took_nanos", 0)
                        if took_nanos > 0:
                            result[f"{phase_name}.took_ms"] = took_nanos / 1_000_000  # Convert to milliseconds

            # Extract driver-level metrics
            drivers = profile.get("drivers", [])
            for driver in drivers:
                driver_name = driver.get("description", "unknown")

                # Add number of drivers
                driver_number_name = f"{driver_name}.number"
                result[driver_number_name] = result.get(driver_number_name, 0) + 1

                # Add driver-level timing metrics
                for metric in ["took", "cpu"]:
                    result_metric_name = f"{driver_name}.{metric}_ms"
                    metric_value = result.get(result_metric_name, 0)
                    result[result_metric_name] = metric_value + driver.get(f"{metric}_nanos", 0) / 1_000_000  # Convert to milliseconds

                # Extract operator-level metrics
                operators = driver.get("operators", [])
                for idx, operator in enumerate(operators):
                    operator_name = operator.get("operator", f"operator_{idx}")
                    # Sanitize operator name for use as a metric key (remove brackets)
                    safe_operator_name = operator_name.split("[")[0] if "[" in operator_name else operator_name

                    # Get process_nanos and cpu_nanos from operator status
                    status = operator.get("status", {})

                    process_nanos = status.get("process_nanos", 0)
                    if process_nanos > 0:
                        metric_key = f"{driver_name}.{safe_operator_name}.process_ms"
                        result[metric_key] = result.get(metric_key, 0) + process_nanos / 1_000_000  # Convert to milliseconds

                    processed_slices = status.get("processed_slices", 0)
                    if processed_slices > 0:
                        metric_key = f"{driver_name}.{safe_operator_name}.processed_slices"
                        result[metric_key] = result.get(metric_key, 0) + processed_slices

            # Extract plan-level metrics
            plans = profile.get("plans", [])
            for plan in plans:
                plan_name = plan.get("description", "unknown")

                # Extract optimization level metrics
                for optimization in ["logical_optimization_nanos", "physical_optimization_nanos", "reduction_nanos"]:
                    optimization_nanos = plan.get(optimization, 0)
                    if optimization_nanos > 0:
                        # Remove "_nanos" suffix from the metric name
                        metric_name = optimization.replace("_nanos", "")
                        metric_key = f"{plan_name}.{metric_name}.took_ms"
                        result[metric_key] = result.get(metric_key, 0) + optimization_nanos / 1_000_000  # Convert to milliseconds

        except Exception as e:
            result["error"] = f"{type(e).__name__}: {str(e)}"

        return result

    def __repr__(self, *args, **kwargs):
        return "esql-profile"


def register(registry):
    registry.register_param_source("initial-indices-source", InitialIndicesParamSource)
    registry.register_param_source("add-track-path", parameter_sources.add_track_path)

    registry.register_param_source("component-template-source", ComponentTemplateParamSource)
    registry.register_param_source("composable-template-source", ComposableTemplateParamSource)

    registry.register_param_source("datastream-source", DataStreamParamSource)
    registry.register_param_source("create-datastream-source", CreateDataStreamParamSource)
    registry.register_runner("create-datastream", datastream.create, async_runner=True)
    registry.register_runner("compression-statistics", datastream.compression_stats, async_runner=True)
    registry.register_runner("check-datastream", datastream.check_health, async_runner=True)
    registry.register_runner("rollover-datastream", datastream.rollover, async_runner=True)
    registry.register_runner("set-shards-datastream", datastream.shards, async_runner=True)
    registry.register_runner("delete-remote-datastream", datastream.DeleteRemoteDataStream(), async_runner=True)
    registry.register_runner("update-custom-templates", update_custom_templates, async_runner=True)
    registry.register_runner("validate-package-assets", validate_package_assets, async_runner=True)

    registry.register_param_source("processed-source", ProcessedCorpusParamSource)

    registry.register_runner("create-ilm", create_ilm, async_runner=True)
    registry.register_runner("create-slm", create_slm, async_runner=True)

    registry.register_runner("create-pipeline", create_pipeline, async_runner=True)

    registry.register_runner("raw-bulk", RawBulkIndex(), async_runner=True)

    registry.register_runner("mount-searchable-snapshot", snapshot.mount, async_runner=True)

    registry.register_scheduler("workflow-scheduler", WorkflowScheduler)
    registry.register_scheduler("timestamp-throttler", TimestampThrottler)

    registry.register_param_source("workflow-selector", WorkflowSelectorParamSource)

    registry.register_param_source("track-params-source", TrackParamSource)

    registry.register_track_processor(TrackIdGenerator())
    registry.register_track_processor(data_generator.DataGenerator())

    registry.register_runner("configure-remote-clusters", ConfigureRemoteClusters(), async_runner=True)
    registry.register_runner("configure-ccr", ConfigureCrossClusterReplication(), async_runner=True)
    registry.register_runner("multi-cluster-wrapper", MultiClusterWrapper(), async_runner=True)

    registry.register_runner("setup-local-remote", setup_local_remote, async_runner=True)

    registry.register_runner("start-reindex-data-stream", StartReindexDataStream(), async_runner=True)
    registry.register_runner("wait-for-reindex-data-stream", WaitForReindexDataStream(), async_runner=True)

    registry.register_runner("esql-profile", EsqlProfileRunner(), async_runner=True)

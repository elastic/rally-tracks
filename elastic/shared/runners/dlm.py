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

import asyncio
import logging

from shared.utils.track import mandatory

"""
Provides operations for Data Lifecycle Management (DLM) on data streams.
"""


async def put_lifecycle(es, params):
    """
    Configure data lifecycle management on a data stream.

    Parameters:
    - data-stream: Name of the data stream (supports wildcards)
    - data_retention: Optional retention period (e.g., "7d", "30d")
    - enabled: Optional boolean to enable/disable lifecycle (default: true)
    - downsampling: Optional dict for downsampling configuration

    Returns: Number of data streams configured
    """
    logger = logging.getLogger(__name__)
    data_stream = mandatory(params, "data-stream", "put-lifecycle")

    # Build lifecycle configuration
    lifecycle_config = {}

    if "data_retention" in params:
        lifecycle_config["data_retention"] = params["data_retention"]

    if "enabled" in params:
        lifecycle_config["enabled"] = params["enabled"]

    if "downsampling" in params:
        lifecycle_config["downsampling"] = params["downsampling"]

    logger.info(f"Configuring lifecycle on data stream [{data_stream}]: {lifecycle_config}")

    # Get all data streams matching the pattern
    try:
        response = await es.indices.get_data_stream(name=data_stream)
        data_streams = [ds["name"] for ds in response["data_streams"]]
    except Exception as e:
        logger.error(f"Failed to get data streams matching [{data_stream}]: {e}")
        raise

    ops = 0
    for ds_name in data_streams:
        try:
            await es.perform_request(method="PUT", path=f"/_data_stream/{ds_name}/_lifecycle", body=lifecycle_config)
            logger.debug(f"Configured lifecycle on [{ds_name}]")
            ops += 1
        except Exception as e:
            logger.error(f"Failed to configure lifecycle on [{ds_name}]: {e}")
            raise

    return ops, "ops"

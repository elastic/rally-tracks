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
import os
from pathlib import Path

async def create_pipeline(es, params):
    pipeline_num = 0
    path = Path(os.path.join(params.get("track-path"), params.get("pipelines", "pipelines")))
    for p in path.rglob("*.json"):
        pipeline_name = os.path.splitext(os.path.basename(p))[0]
        with open(p, "r") as pipeline_file:
            pipeline = json.load(pipeline_file)
            await es.ingest.put_pipeline(pipeline_name, body=pipeline)
            pipeline_num += 1
    return pipeline_num, "ops"

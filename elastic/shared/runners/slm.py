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
import glob
import json
import os

from elasticsearch.client import SlmClient


async def create_slm(es, params):
    slm = SlmClient(es)
    policy_num = 0
    for policy_path in glob.glob(os.path.join(params.get("track-path"), params.get("policies", "slm"), "*.json")):
        policy_name = os.path.splitext(os.path.basename(policy_path))[0]
        with open(policy_path, "r") as policy_file:
            policy = json.load(policy_file)
        await slm.put_lifecycle(policy_id=policy_name, body=policy)
        policy_num += 1
    return policy_num, "ops"

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

BASE_PARAMS = {
    "start_date": "2021-01-01T00-00-00Z",
    "end_date": "2021-01-01T00-01-00Z",
    "max_total_download_gb": "18",
    "raw_data_volume_per_day": "72GB",
    "max_generated_corpus_size": "1GB",
    "wait_for_status": "green",
    "force_data_generation": "true",
    "number_of_shards": "2",
    "number_of_replicas": "0",
}


def params(updates=None):
    base = BASE_PARAMS.copy()
    if updates is None:
        return base
    else:
        return {**base, **updates}

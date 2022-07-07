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

from esrally.driver.runner import BulkIndex


class RawBulkIndex(BulkIndex):
    """
    Bulk indexes the given documents and provides enhanced stats on the raw data and index lag for throughput analysis.
    """

    def __init__(self):
        super().__init__()

    def detailed_stats(self, params, response):
        """
        Provides the same detailed response as the Bulk Runner base implementation but adds additional metrics
        regarding the message size field (the raw size) as well as how far the indexed data is ahead or behind
        the actual data (in relative seconds). In this case of throttling this should be close to 0 but in other
        cases we might lag or be ahead depending on the cluster/load drivers ability to keep up.
        """
        stats = super().detailed_stats(params, response)
        return {**stats, **params["param-source-stats"]}

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
import hashlib

from esrally import exceptions

global_config = {}


# This doesn't produce a reliable value across clients or restarts. Ideally we need a hash of the rendered track json.
def generate_track_id(track):
    m = hashlib.md5()
    m.update(repr(track).encode("utf-8"))
    return m.hexdigest()


def mandatory(params, key, op):
    try:
        return params[key]
    except KeyError:
        raise exceptions.DataError(
            f"Parameter source for operation '{str(op)}' did not provide the mandatory parameter '{key}'. "
            f"Add it to your parameter source and try again."
        )

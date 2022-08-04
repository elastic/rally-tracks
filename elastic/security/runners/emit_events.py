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
import logging

logger = logging.getLogger(__name__)


async def emit_events(es, params):
    count = 0

    for batch in params["doc-batches"]:
        bulk = []

        for event in batch:
            bulk.append(json.dumps({"index": {"_index": event.meta["index"]}}))
            bulk.append(json.dumps(event.doc))

        ret = await es.bulk(body="\n".join(bulk), request_timeout=params["request-timeout"])
        errors = [item["index"] for item in ret["items"] if item["index"]["status"] != 201]
        if errors:
            msg = "\n  ".join(str(err) for err in errors)
            raise RuntimeError(f"Got {len(errors)} ingestion error(s):\n  {msg}")

        count += len(ret["items"])

    return count, "docs"

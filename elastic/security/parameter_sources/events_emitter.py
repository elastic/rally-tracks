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

import os
import shutil
import logging
from glob import glob
from fnmatch import fnmatch
from urllib.parse import urlparse
from itertools import chain, islice
from contextlib import contextmanager
from types import SimpleNamespace
from tempfile import mkdtemp

import esrally

logger = logging.getLogger(__name__)


def set_to_lower(iterable):
    return set(x.lower() for x in iterable)


@contextmanager
def resource(track, uri):
    tmpdir = mkdtemp()
    uri_parts = urlparse(uri)

    if uri_parts.scheme.startswith("http"):
        uri_file = uri_parts.path.split("/")[-1]
        local_file = os.path.join(tmpdir, uri_file)
        esrally.utils.net.download_http(uri, local_file)
    elif uri_parts.scheme == "file":
        if uri_parts.netloc == '.':
            local_file = os.path.join(track.root, "." + uri_parts.path)
        else:
            local_file = uri_parts.path
    else:
        raise ValueError(f"uri scheme not supported: {uri_parts.scheme}")

    shutil.unpack_archive(local_file, tmpdir)

    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir)


def load_schema(track, params):
    if "schema" not in params:
        raise ValueError("Required param 'schema' is not configured")
    if "uri" not in params["schema"]:
        raise ValueError("Required param 'schema.uri' is not configured")
    if "path" not in params["schema"]:
        raise ValueError("Required param 'schema.path' is not configured")

    with resource(track, params["schema"]["uri"]) as resource_dir:
        files = glob(os.path.join(resource_dir, "*", params["schema"]["path"]), recursive=True)
        if len(files) < 1:
            raise ValueError(f"File not found in '{resource_dir}': '{params['schema']['path']}'")
        if len(files) > 1:
            raise ValueError(f"Too many files: {files}")

        logger.info(f"schema: {files[0]}")
        with open(files[0]) as f:
            import yaml
            return yaml.safe_load(f)


def load_rules(track, params):
    if "uri" not in params["rules"]:
        raise ValueError("Required param 'rules.uri' is not configured")
    if "path" not in params["rules"]:
        raise ValueError("Required param 'rules.path' is not configured")

    tags = set_to_lower(params["rules"].get("tags", []))
    logger.info(f"Rule tags: {', '.join(sorted(tags)) or '<none>'}")

    with resource(track, params["rules"]["uri"]) as resource_dir:
        import pytoml

        for filename in glob(os.path.join(resource_dir, "*", params["rules"]["path"]), recursive=True):
            try:
                with open(filename) as f:
                    rule = pytoml.load(f)["rule"]
            except Exception as e:
                logger.error(f"[{e}] while loading from [{filename}]")
                continue

            if rule["type"] not in ("eql", "query") or rule["language"] not in ("eql", "kuery"):
                continue
            if tags and not (tags & set_to_lower(rule.get("tags", []))):
                continue
            rule["index"] = [str(ds) for ds in track.data_streams for idx in rule["index"] if fnmatch(str(ds), idx)]
            if not rule["index"]:
                continue

            rule["filename"] = filename
            yield SimpleNamespace(**rule)


def batch_sizes(total_count, batch_size):
    while total_count:
        this_batch_size = min(total_count, batch_size)
        total_count -= this_batch_size
        yield this_batch_size


def batches(iterable, total_count, batch_size):
    for this_batch_size in batch_sizes(total_count, batch_size):
        yield chain(*islice(iterable, this_batch_size))


class EventsEmitterParamSource:
    def __init__(self, track, params, **kwargs):
        from geneve import SourceEvents

        schema = kwargs["_test_schema"] if "_test_schema" in kwargs else load_schema(track, params)
        self.source_events = SourceEvents(schema)
        self.index = params.get("index", None)
        self.bulk_batch_size = params.get("bulk-batch-size", 100)
        self.request_timeout = params.get("request-timeout", None)
        self.number_of_alerts = params["number-of-alerts"]
        index_stats = {}

        if "rules" not in params and "queries" not in params:
            raise ValueError("Either param 'rules' or 'queries' must be configured")

        if "rules" in params:
            for rule in load_rules(track, params):
                index = self.index or rule.index[0]

                try:
                    self.source_events.add_rule(rule, meta={"index": index})
                except Exception as e:
                    logger.error(f"[{e}] while adding rule [{rule.filename}]")
                    continue

                if index not in index_stats:
                    index_stats[index] = 1
                else:
                    index_stats[index] += 1

        if "queries" in params:
            if not self.index:
                raise ValueError("Param 'queries' requires param 'index' to be configured")

            for query in params.get("queries", []):
                try:
                    self.source_events.add_query(query, meta={"index": self.index})
                except Exception as e:
                    logger.error(f"[{e}] while adding query [{query}]")
                    continue

                if self.index not in index_stats:
                    index_stats[self.index] = 0
                else:
                    index_stats[self.index] += 1

        if not self.source_events:
            raise ValueError("No valid rules or queries were loaded")

        logger.info(f"Loaded {len(self.source_events)} roots")
        for index in sorted(index_stats):
            logger.info(f"Index {index}: {index_stats[index]}")

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        doc_batches = batches(self.source_events, self.number_of_alerts, self.bulk_batch_size)
        return {
            "doc-batches": doc_batches,
            "request-timeout": self.request_timeout,
        }

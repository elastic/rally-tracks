import csv
import os
import random
import json


class QueryParamSource:
    # We need to stick to the param source API
    # noinspection PyUnusedLocal
    def __init__(self, track, params, **kwargs):
        self._params = params
        self.infinite = True
        self.query_text = []
        self._param_variants = []

        # be predictably random. The seed has been chosen by a fair dice roll. ;)
        random.seed(4)
        cwd = os.path.dirname(__file__)

        params_file = self._params.get("params_file")
        if params_file:
            params_path = params_file if os.path.isabs(params_file) else os.path.join(cwd, params_file)
            with open(params_path, "r") as ins:
                param_data = json.load(ins)

            if isinstance(param_data, dict):
                if "params" in param_data and isinstance(param_data["params"], dict):
                    param_data = [param_data["params"]]
                else:
                    param_data = [param_data]
            elif not isinstance(param_data, list):
                raise ValueError("params_file must contain a JSON object or array of objects")

            self._param_variants = []
            for entry in param_data:
                if not isinstance(entry, dict):
                    raise ValueError("Each entry in params_file must be a JSON object")
                self._param_variants.append(entry)

        queries_file = self._params.get("queries_file")
        query_path = queries_file if os.path.isabs(queries_file) else os.path.join(cwd, queries_file)

        with open(query_path, "r") as ins:
            csvreader = csv.reader(ins)
            for row in csvreader:
                if not row:
                    continue
                value = row[0].strip()
                if value:
                    self.query_text.append(value)

        if not self.query_text:
            raise ValueError(f"No query values found in {query_path}")

    # We need to stick to the param source API
    # noinspection PyUnusedLocal
    def partition(self, partition_index, total_partitions):
        return self


class RandomParamSource(QueryParamSource):
    def _template_params(self, random_query):
        template_params = {}

        if self._param_variants:
            template_params.update(random.choice(self._param_variants))

        template_params.setdefault("query_string", random_query)

        reserved = {
            "index",
            "search_template",
            "cache",
            "queries_file",
            "params_file",
        }

        for key, value in self._params.items():
            if key not in reserved and key not in template_params:
                template_params[key] = value

        return template_params

    def params(self):
        random_query = random.choice(self.query_text)
        index = self._params["index"]

        result = {
            "method": "POST",
            "path": f"/{index.lstrip('/')}\/_search\/template",
            "body": {
                "id": self._params["search_template"],
                "params": self._template_params(random_query),
            },
        }

        if "cache" in self._params:
            result["cache"] = self._params["cache"]

        return result


def register(registry):
    registry.register_param_source("random_query_text", RandomParamSource)

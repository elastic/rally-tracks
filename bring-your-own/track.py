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
        # here we read the queries data file into arrays which we'll then later use randomly.
        self.query_text = []
        # be predictably random. The seed has been chosen by a fair dice roll. ;)
        random.seed(4)
        cwd = os.path.dirname(__file__)
        with open(os.path.join(cwd, "queries.csv"), "r") as ins:
            csvreader = csv.reader(ins)
            for row in csvreader:
                self.query_text.append(row[0])
    # We need to stick to the param source API
    # noinspection PyUnusedLocal
    def partition(self, partition_index, total_partitions):
        return self
class RandomParamSource(QueryParamSource):
    def params(self):
        random_query = random.choice(self.query_text)
        index = self._params["index"]

        result = {
            "body": {
                "id": self._params["search_template"],
                "params": {
                    "query_string": random_query
                }
            },
            "path": "/"+index+"/_search/template"
        }

        if "cache" in self._params:
            result["cache"] = self._params["cache"]
        #print("DEBUG:", json.dumps(result, indent=2))
        return result

def register(registry):
    registry.register_param_source("random_query_text", RandomParamSource)

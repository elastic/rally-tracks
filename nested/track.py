import random
import os
import csv

class QueryParamSource:
    def __init__(self, indices, params):
        self._indices = indices
        self._params = params
        # here we read the queries data file into arrays which we'll then later use randomly.
        self.tags = []
        self.dates = []
        # be predictably random. The seed has been chosen by a fair dice roll. ;)
        random.seed(4)
        cwd = os.path.dirname(__file__)
        with open(os.path.join(cwd, "queries.csv"), "r") as ins:
            csvreader = csv.reader(ins)
            for row in csvreader:
                self.tags.append(row[0])
                self.dates.append(row[1])

    def partition(self, partition_index, total_partitions):
        return self

    def size(self):
        return 1

class TermQueryParamSource(QueryParamSource):

    def params(self):
        result = {
            "body": {
                "query": {
                    "match": {
                        "tag": "%s" % random.choice(self.tags)
                    }
                },
                "sort": [
                    {
                        "answers.date": {
                            "mode" :  "max",
                            "order": "desc",
                            "nested_path": "answers"
                        }
                    }
                ]
            },
            "index": None,
            "type": None,
            "use_request_cache": self._params["use_request_cache"]
        }
        return result

class SortedTermQueryParamSource(QueryParamSource):

    def params(self):
        result = {
            "body": {
                "query": {
                    "match": {
                        "tag": "%s" % random.choice(self.tags)
                    }
                }
            },
            "index": None,
            "type": None,
            "use_request_cache": self._params["use_request_cache"]
        }
        return result

class NestedQueryParamSource(QueryParamSource):

    def params(self):
        result = {
            "body": {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "tag": "%s" % random.choice(self.tags)
                                }
                            },
                            {
                                "nested": {
                                    "path": "answers",
                                    "query": {
                                        "range": {
                                            "answers.date": {
                                                "lte": "%s" % random.choice(self.dates)
                                             }
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            },
            "index": None,
            "type": None,
            "use_request_cache": self._params["use_request_cache"]
        }
        return result


def register(registry):
    registry.register_param_source("nested-query-source", NestedQueryParamSource)
    registry.register_param_source("term-query-source", TermQueryParamSource)
    registry.register_param_source("sorted-term-query-source", SortedTermQueryParamSource)

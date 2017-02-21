import random
import os
import csv

class QueryParamSource:
    def __init__(self, indices, params):
        self._indices = indices
        self._params = params
        # here we read the queries data file into arrays which we'll then later use randomly.
        self.tags = []
        self.users = []
        self.dates = []
        cwd = os.path.dirname(__file__)
        with open(os.path.join(cwd, "queries.csv"), "r") as ins:
            csvreader = csv.reader(ins)        
            for row in csvreader:
                self.tags.append(row[0])
                self.users.append(row[1])
                self.dates.append(row[2])

    def partition(self, partition_index, total_partitions):
        return self

    def size(self):
        return 1

    def params(self):
        result= {
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
                                 "bool": {
                                     "must": [
                                         {
                                            "range": {
                                                "answers.date": {
                                                   "lte":  "%s" % random.choice(self.dates)
                                                }
                                         }
                                        },
                                         {
                                            "term": {
                                                "answers.user":  "%s" % random.choice(self.users)
                                         }
                                        },
                                    ]
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
            "use_request_cache": False
        }
        return result


def register(registry):
    registry.register_param_source("nested-query-source", QueryParamSource)

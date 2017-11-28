import random
import os


class QueryParamSource:
    def __init__(self, indices, params):
        self._indices = indices
        self._params = params
        cwd = os.path.dirname(__file__)
        # The terms.txt file has been generated with:
        # sed -n '13~250p' [path_to_rally_data]/geonames/documents.json | shuf | sed -e "s/.*name\": \"//;s/\",.*$//" > terms.txt
        with open(os.path.join(cwd, "terms.txt"), "r") as ins:
            self.terms = [line.strip() for line in ins.readlines()]

    def partition(self, partition_index, total_partitions):
        return self

    def size(self):
        return 1


class PureTermsQueryParamSource(QueryParamSource):
    def params(self):
        query_terms = list(self.terms)  # copy
        query_terms.append(str(random.randint(1, 100)))  # avoid caching
        result = {
            "body": {
                "query": {
                    "terms": {
                        "name.raw": query_terms
                    }
                }
            },
            "index": None,
            "type": None,
            "use_request_cache": self._params.get("use_request_cache", False)
        }
        return result


class FilteredTermsQueryParamSource(QueryParamSource):
    def params(self):
        query_terms = list(self.terms)  # copy
        query_terms.append(str(random.randint(1, 1000)))  # avoid caching
        result = {
            "body": {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "feature_class.raw": "T"
                                }
                            }
                        ],
                        "filter": [
                            {
                                "terms": {
                                    "name.raw": query_terms
                                }
                            }
                        ]
                    }
                }
            },
            "index": None,
            "type": None,
            "use_request_cache": self._params.get("use_request_cache", False)
        }
        return result


class ProhibitedTermsQueryParamSource(QueryParamSource):
    def params(self):
        query_terms = list(self.terms)  # copy
        query_terms.append(str(random.randint(1, 1000)))  # avoid caching
        result = {
            "body": {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "feature_class.raw": "A"
                                }
                            }
                        ],
                        "must_not": [
                            {
                                "terms": {
                                    "name.raw": query_terms
                                }
                            }
                        ]
                    }
                }
            },
            "index": None,
            "type": None,
            "use_request_cache": self._params.get("use_request_cache", False)
        }
        return result

def refresh(es, params):
    es.indices.refresh(index=params.get("index", "_all"))


def register(registry):
    registry.register_param_source("pure-terms-query-source", PureTermsQueryParamSource)
    registry.register_param_source("filtered-terms-query-source", FilteredTermsQueryParamSource)
    registry.register_param_source("prohibited-terms-query-source", ProhibitedTermsQueryParamSource)
    registry.register_runner("refresh", refresh)

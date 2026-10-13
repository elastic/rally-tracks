import random


def register(registry):
    registry.register_param_source("search-param-source", SearchParamSource)


class SearchParamSource:
    """
    Reads article titles from a per-language query file and emits
    the appropriate query body depending on the model param:
      - elser / jina  → semantic query on the content field
      - bm25          → match query on content + title
    """

    def __init__(self, track, params, **kwargs):
        import os
        self._model = params.get("model", "bm25")
        track_root = os.path.dirname(os.path.abspath(__file__))

        # Load queries from all three languages into one pool
        self._queries = []
        for lang in ("en", "es", "dv"):
            query_path = os.path.join(track_root, "data", f"queries_{lang}.txt")
            with open(query_path, encoding="utf-8") as f:
                self._queries.extend(line.strip() for line in f if line.strip())

        self._index = params.get("index", f"wiki-{self._model}")
        self._size = params.get("results_size", 10)

    def partition(self, partition_index, total_partitions):
        return self

    def params(self):
        query_text = random.choice(self._queries)
        if self._model in ("elser", "jina"):
            body = {
                "query": {
                    "semantic": {
                        "field": "content",
                        "query": query_text
                    }
                },
                "size": self._size
            }
        else:
            body = {
                "query": {
                    "multi_match": {
                        "query": query_text,
                        "fields": ["title^2", "content"]
                    }
                },
                "size": self._size
            }
        return {
            "index": self._index,
            "type": None,
            "cache": False,
            "body": body
        }

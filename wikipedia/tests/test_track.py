import dataclasses

from wikipedia import track


def test_query_samples():
    queries = track.query_samples(100, 123)
    assert len(queries) == 100


def test_RandomQueriesParamSource_query():
    """It tests DummyRandomQueriesParamSource.query() will return the same random sequence twice by calling N*2 times query method."""
    want = track.query_samples(3, 123) * 2

    source = DummyRandomQueriesParamSource(track=None, params={"batch_size": 3, "seed": 123})
    got = [source.query() for _ in want]
    assert got == want


def test_SearchApplicationSearchParamSource_params():
    """It tests SearchApplicationSearchParamSource.params()."""

    want = [
        {
            "body": {"params": {"query_string": query}},
            "method": "POST",
            "path": "/_application/search_application/dummy-search-application/_search",
        }
        for query in track.query_samples(2, 321)
    ] * 2  # It will iterate this twice.

    source = track.SearchApplicationSearchParamSource(DummyTrack(), params={"batch_size": 2, "seed": 321})
    got = [source.params() for _ in want]
    assert got == want


def test_QueryRulesSearchParamSource_params():
    want = [
        {
            "body": {
                "query": {
                    "rule": {
                        "match_criteria": {"rule_key": AnyOf(["match", "no-match"])},
                        "organic": {"query_string": {"default_field": ["<search-field>"], "query": query}},
                        "ruleset_ids": [None],
                    }
                },
                "size": 10,
            },
            "method": "POST",
            "path": "/_search",
        }
        for query in track.query_samples(2, 321)
    ] * 2  # It will iterate this twice.

    source = track.QueryRulesSearchParamSource(
        track=DummyTrack(), params={"batch_size": 2, "seed": 321, "search-fields": ["<search-field>"], "size": 10}
    )
    got = [source.params() for _ in want]
    assert want == got


def test_PinnedSearchParamSource_params():
    ids = track.ids_samples()
    want = [
        {
            "body": {
                "query": {
                    "pinned": {"ids": [AnyOf(ids)], "organic": {"query_string": {"default_field": ["<search-field>"], "query": query}}}
                },
                "size": 10,
            },
            "method": "POST",
            "path": "/_search",
        }
        for query in track.query_samples(2, 321)
    ] * 2  # It will iterate this twice.

    source = track.PinnedSearchParamSource(
        track=DummyTrack(), params={"batch_size": 2, "seed": 321, "search-fields": ["<search-field>"], "size": 10}
    )
    got = [source.params() for _ in want]
    assert got == want


def test_RetrieverParamSource_params():
    want = [
        {
            "body": {
                "retriever": {"standard": {"query": {"query_string": {"default_field": ["<search-field>"], "query": query}}}},
                "size": 10,
            },
            "method": "POST",
            "path": "/dummy/_search",
        }
        for query in track.query_samples(2, 321)
    ] * 2  # It will iterate this twice.

    source = track.RetrieverParamSource(
        track=DummyTrack(), params={"batch_size": 2, "seed": 321, "search-fields": ["<search-field>"], "size": 10}
    )
    got = [source.params() for _ in want]
    assert got == want


def test_QueryParamSource_params():
    want = [
        {
            "body": {"query": {"query_string": {"default_field": ["<search-fields>"], "query": query}}, "size": 2},
            "cache": True,
            "index": "dummy",
        }
        for query in track.query_samples(2, 321)
    ] * 2  # It will iterate this twice.

    source = track.QueryParamSource(
        track=DummyTrack(),
        params={"batch_size": 2, "seed": 321, "query-type": "query-string", "search-fields": ["<search-fields>"], "size": 2},
    )
    got = [source.params() for _ in want]
    assert got == want


@dataclasses.dataclass()
class DummyIndex:
    name: str = "dummy"


@dataclasses.dataclass()
class DummyTrack:
    indices: tuple[DummyIndex, ...] = (DummyIndex(),)

    def index_names(self) -> list[str]:
        return [i.name for i in self.indices]


class DummyRandomQueriesParamSource(track.RandomQueriesParamSource):
    # Dummy implementation of abstract method.
    def params(self):
        return {"query": self.query()}


class AnyOf(list):
    def __eq__(self, other) -> bool:
        return other in self

    def __repr__(self) -> str:
        return f"AnyOf([{self[0]}, ...])"

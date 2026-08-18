import importlib.util
import json
import pathlib

TRACK_PATH = pathlib.Path(__file__).resolve().parents[1] / "track.py"
SPEC = importlib.util.spec_from_file_location("bring_your_own_track", TRACK_PATH)
TRACK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TRACK)


def test_random_query_source_has_query_string_only_when_no_params_file_is_used(monkeypatch):
    original_isfile = TRACK.os.path.isfile

    def patched_isfile(path):
        if path.endswith("params.json"):
            return False
        return original_isfile(path)

    monkeypatch.setattr(TRACK.os.path, "isfile", patched_isfile)

    params = {
        "index": "my_index",
        "search_template": "my_template",
        "queries_file": "queries.csv",
    }

    source = TRACK.RandomParamSource(None, params)
    result = source.params()

    assert result["method"] == "POST"
    assert result["path"] == "/my_index/_search/template"
    assert "query_string" in result["body"]["params"]
    assert "from" not in result["body"]["params"]
    assert "size" not in result["body"]["params"]


def test_bundled_sample_files_are_used_when_track_params_are_omitted():
    params = {
        "index": "my_index",
        "search_template": "my_template",
    }

    source = TRACK.RandomParamSource(None, params)
    result = source.params()

    assert result["method"] == "POST"
    assert result["path"] == "/my_index/_search/template"
    assert result["body"]["params"]["query_string"]
    assert result["body"]["params"]["from"] == 0
    assert result["body"]["params"]["size"] == 5


def test_params_file_overrides_template_values(tmp_path):
    params_path = tmp_path / "params.json"
    params_path.write_text(
        json.dumps(
            {
                "query_string": "Paris",
                "from": 2,
                "size": 5,
                "tenant": "acme",
            }
        )
    )

    params = {
        "index": "my_index",
        "search_template": "my_search_template",
        "queries_file": "queries.csv",
        "params_file": str(params_path),
    }

    source = TRACK.RandomParamSource(None, params)
    result = source.params()

    assert result["body"]["params"]["query_string"] == "Paris"
    assert result["body"]["params"]["from"] == 2
    assert result["body"]["params"]["size"] == 5
    assert result["body"]["params"]["tenant"] == "acme"

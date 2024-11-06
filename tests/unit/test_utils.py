import pathlib
import tempfile
import typing
import unittest.mock

import pytest

from recordlinker import utils
from recordlinker.linking import matchers


def test_project_root():
    root = utils.project_root()
    assert root.name == "recordlinker"

def test_project_root_not_found():
    with unittest.mock.patch("pathlib.Path.resolve") as mock_resolve:
        mock_resolve.return_value = pathlib.Path("/")
        with pytest.raises(FileNotFoundError):
            utils.project_root()

def test_read_json_relative():
    tmp = utils.project_root() / "test.json"
    with open(tmp, "w") as fobj:
        fobj.write('{"key": "value"}')
    assert utils.read_json("test.json") == {"key": "value"}
    tmp.unlink()

def test_read_json_absolute():
    tmp = tempfile.NamedTemporaryFile(suffix=".json")
    with open(tmp.name, "w") as fobj:
        fobj.write('{"key": "value"}')
    assert utils.read_json(tmp.name) == {"key": "value"}
    tmp.close()


def test_bind_functions():
    funcs = {
        "first_name": "func:recordlinker.linking.matchers.feature_match_fuzzy_string",
        "last_name": "func:recordlinker.linking.matchers.feature_match_exact",
    }
    assert utils.bind_functions(funcs) == {
        "first_name": matchers.feature_match_fuzzy_string,
        "last_name": matchers.feature_match_exact,
    }

    funcs = {
        "blocks": [
            {"value": "birthdate"},
            {"value": "func:recordlinker.linking.matchers.feature_match_exact"},
        ]
    }
    assert utils.bind_functions(funcs) == {
        "blocks": [
            {"value": "birthdate"},
            {"value": matchers.feature_match_exact},
        ]
    }

    funcs = {
        "nested": {
            "first_name": "func:recordlinker.linking.matchers.feature_match_fuzzy_string",
            "last_name": "func:recordlinker.linking.matchers.feature_match_exact",
        }
    }
    assert utils.bind_functions(funcs) == {
        "nested": {
            "first_name": matchers.feature_match_fuzzy_string,
            "last_name": matchers.feature_match_exact,
        }
    }


def test_str_to_callable():
    val = "func:recordlinker.linking.matchers.feature_match_exact"
    assert utils.str_to_callable(val) == matchers.feature_match_exact
    val = "recordlinker.linking.matchers.feature_match_exact"
    assert utils.str_to_callable(val) == matchers.feature_match_exact
    val = "recordlinker.unknown_module.unknown_function"
    with pytest.raises(ValueError):
        utils.str_to_callable(val)
    val = "recordlinker.linking.matchers.unknown_function"
    with pytest.raises(ValueError):
        utils.str_to_callable(val)


def test_func_to_str():
    assert (
        utils.func_to_str(matchers.feature_match_exact)
        == "func:recordlinker.linking.matchers.feature_match_exact"
    )
    assert (
        utils.func_to_str(matchers.feature_match_fuzzy_string)
        == "func:recordlinker.linking.matchers.feature_match_fuzzy_string"
    )


class TestCheckSignature:
    @staticmethod
    def func1(a: int, b: str) -> None:
        pass

    @staticmethod
    def func2(a: int, b: list[int]) -> float:
        pass

    def test_check_signature(self):
        assert not utils.check_signature(self.func1, typing.Callable[[str], str])
        assert not utils.check_signature(self.func1, typing.Callable[[int, str], str])
        assert utils.check_signature(self.func1, typing.Callable[[int, str], None])
        assert not utils.check_signature(self.func2, typing.Callable[[int, int], float])
        assert not utils.check_signature(self.func2, typing.Callable[[int, list], float])
        assert not utils.check_signature(self.func2, typing.Callable[[int, list[int]], None])
        assert utils.check_signature(self.func2, typing.Callable[[int, list[int]], float])
        assert not utils.check_signature("a", typing.Callable[[str], None])


class TestMockTracer:
    def test_start_span(self):
        tracer = utils.MockTracer()
        with tracer.start_span("test_span") as span:
            assert span is None

    def test_start_as_current_span(self):
        tracer = utils.MockTracer()
        with tracer.start_as_current_span("test.span") as span:
            assert span is None

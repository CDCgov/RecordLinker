import pytest

from recordlinker.linking import matchers
from recordlinker.utils import functools as utils


def test_bind_functions():
    funcs = {
        "first_name": "func:recordlinker.linking.matchers.compare_fuzzy_match",
        "last_name": "func:recordlinker.linking.matchers.compare_match_all",
    }
    assert utils.bind_functions(funcs) == {
        "first_name": matchers.compare_fuzzy_match,
        "last_name": matchers.compare_match_all,
    }

    funcs = {
        "blocks": [
            {"value": "birthdate"},
            {"value": "func:recordlinker.linking.matchers.compare_match_all"},
        ]
    }
    assert utils.bind_functions(funcs) == {
        "blocks": [
            {"value": "birthdate"},
            {"value": matchers.compare_match_all},
        ]
    }

    funcs = {
        "nested": {
            "first_name": "func:recordlinker.linking.matchers.compare_fuzzy_match",
            "last_name": "func:recordlinker.linking.matchers.compare_match_all",
        }
    }
    assert utils.bind_functions(funcs) == {
        "nested": {
            "first_name": matchers.compare_fuzzy_match,
            "last_name": matchers.compare_match_all,
        }
    }


def test_str_to_callable():
    val = "func:recordlinker.linking.matchers.compare_match_all"
    assert utils.str_to_callable(val) == matchers.compare_match_all
    val = "recordlinker.linking.matchers.compare_match_all"
    assert utils.str_to_callable(val) == matchers.compare_match_all
    val = "recordlinker.unknown_module.unknown_function"
    with pytest.raises(ValueError):
        utils.str_to_callable(val)
    val = "recordlinker.linking.matchers.unknown_function"
    with pytest.raises(ValueError):
        utils.str_to_callable(val)


def test_func_to_str():
    assert (
        utils.func_to_str(matchers.compare_match_all)
        == "func:recordlinker.linking.matchers.compare_match_all"
    )
    assert (
        utils.func_to_str(matchers.compare_fuzzy_match)
        == "func:recordlinker.linking.matchers.compare_fuzzy_match"
    )

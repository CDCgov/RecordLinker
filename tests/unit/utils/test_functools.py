import pytest

from recordlinker.linking import matchers
from recordlinker.utils import functools as utils


def test_bind_functions():
    funcs = {
        "first_name": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match",
        "last_name": "func:recordlinker.linking.matchers.compare_probabilistic_exact_match",
    }
    assert utils.bind_functions(funcs) == {
        "first_name": matchers.compare_probabilistic_fuzzy_match,
        "last_name": matchers.compare_probabilistic_exact_match,
    }

    funcs = {
        "blocks": [
            {"value": "birthdate"},
            {"value": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match"},
        ]
    }
    assert utils.bind_functions(funcs) == {
        "blocks": [
            {"value": "birthdate"},
            {"value": matchers.compare_probabilistic_fuzzy_match},
        ]
    }

    funcs = {
        "nested": {
            "first_name": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match",
            "last_name": "func:recordlinker.linking.matchers.compare_probabilistic_exact_match",
        }
    }
    assert utils.bind_functions(funcs) == {
        "nested": {
            "first_name": matchers.compare_probabilistic_fuzzy_match,
            "last_name": matchers.compare_probabilistic_exact_match,
        }
    }


def test_str_to_callable():
    val = "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match"
    assert utils.str_to_callable(val) == matchers.compare_probabilistic_fuzzy_match
    val = "recordlinker.linking.matchers.compare_probabilistic_exact_match"
    assert utils.str_to_callable(val) == matchers.compare_probabilistic_exact_match
    val = "recordlinker.unknown_module.unknown_function"
    with pytest.raises(ValueError):
        utils.str_to_callable(val)
    val = "recordlinker.linking.matchers.unknown_function"
    with pytest.raises(ValueError):
        utils.str_to_callable(val)


def test_func_to_str():
    assert (
        utils.func_to_str(matchers.compare_probabilistic_fuzzy_match)
        == "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match"
    )
    assert (
        utils.func_to_str(matchers.compare_probabilistic_exact_match)
        == "func:recordlinker.linking.matchers.compare_probabilistic_exact_match"
    )

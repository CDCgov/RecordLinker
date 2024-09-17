from datetime import date
from datetime import datetime

import pytest

from recordlinker.linkage import matchers
from recordlinker.linkage import utils


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        (date(2023, 10, 10), "2023-10-10"),
        (datetime(2023, 10, 10, 15, 30), "2023-10-10"),
        ("2023-10-10", "2023-10-10"),
    ],
)
def test_valid_datetime_to_str(input_value, expected_output):
    assert utils.datetime_to_str(input_value) == expected_output


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        (date(2023, 10, 10), "2023-10-10 00:00:00"),
        (datetime(2023, 10, 10, 15, 30), "2023-10-10 15:30:00"),
        ("2023-10-10 15:30:00", "2023-10-10 15:30:00"),
    ],
)
def test_valid_datetime_to_str_with_time(input_value, expected_output):
    assert utils.datetime_to_str(input_value, include_time=True) == expected_output


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        ("", ""),
        (None, ""),
        (20231010, "20231010"),
        (["2023-10-10"], "['2023-10-10']"),
        ({"date": "2023-10-10"}, "{'date': '2023-10-10'}"),
    ],
)
def test_bad_input_datetime_to_str(input_value, expected_output):
    assert utils.datetime_to_str(input_value) == expected_output


def test_bind_functions():
    funcs = {
        "first_name": "func:recordlinker.linkage.matchers.feature_match_fuzzy_string",
        "last_name": "func:recordlinker.linkage.matchers.feature_match_exact",
    }
    assert utils.bind_functions(funcs) == {
        "first_name": matchers.feature_match_fuzzy_string,
        "last_name": matchers.feature_match_exact,
    }

    funcs = {
        "blocks": [
            {"value": "birthdate"},
            {"value": "func:recordlinker.linkage.matchers.feature_match_exact"},
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
            "first_name": "func:recordlinker.linkage.matchers.feature_match_fuzzy_string",
            "last_name": "func:recordlinker.linkage.matchers.feature_match_exact",
        }
    }
    assert utils.bind_functions(funcs) == {
        "nested": {
            "first_name": matchers.feature_match_fuzzy_string,
            "last_name": matchers.feature_match_exact,
        }
    }


def test_string_to_callable():
    val = "func:recordlinker.linkage.matchers.feature_match_exact"
    assert utils.string_to_callable(val) == matchers.feature_match_exact
    val = "recordlinker.linkage.matchers.feature_match_exact"
    assert utils.string_to_callable(val) == matchers.feature_match_exact
    val = "recordlinker.unknown_module.unknown_function"
    with pytest.raises(ImportError):
        utils.string_to_callable(val)
    val = "recordlinker.linkage.matchers.unknown_function"
    with pytest.raises(AttributeError):
        utils.string_to_callable(val)

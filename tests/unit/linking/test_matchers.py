"""
unit.linking.test_matchers
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains unit tests for the :mod:`~recordlinker.linking.matchers` module.
"""
import inspect
import typing

import pytest

from recordlinker import models
from recordlinker import schemas
from recordlinker.linking import matchers
from recordlinker.utils import functools as utils


class TestRuleFunc:
    def test_correct_signatures(self):
        for rule in matchers.RuleFunc:
            fn = utils.str_to_callable(rule.value)
            assert callable(fn)
            signature = inspect.signature(fn)
            params = list(signature.parameters.values())
            assert len(params) == 2
            assert params[0].annotation == list[float]
            assert params[1].annotation == typing.Any
            assert signature.return_annotation is bool


class TestFeatureFunc:
    def test_correct_signatures(self):
        for rule in matchers.FeatureFunc:
            fn = utils.str_to_callable(rule.value)
            assert callable(fn)
            signature = inspect.signature(fn)
            params = list(signature.parameters.values())
            assert len(params) == 4
            assert params[0].annotation == schemas.PIIRecord
            assert params[1].annotation == models.Patient
            assert params[2].annotation == schemas.Feature
            assert params[3].annotation == typing.Any
            assert signature.return_annotation is float


def test_get_fuzzy_params():
    assert matchers._get_fuzzy_params("last_name") == ("JaroWinkler", 0.7)

    kwargs = {
        "similarity_measure": "Levenshtein",
        "thresholds": {"city": 0.95, "address": 0.98},
    }
    assert matchers._get_fuzzy_params("city", **kwargs) == ("Levenshtein", 0.95)
    assert matchers._get_fuzzy_params("address", **kwargs) == ("Levenshtein", 0.98)
    assert matchers._get_fuzzy_params("first_name", **kwargs) == ("Levenshtein", 0.7)


def test_compare_probabilistic_fuzzy_match():
    with pytest.raises(ValueError):
        matchers.compare_probabilistic_fuzzy_match(
            schemas.PIIRecord(),
            models.Patient(),
            schemas.Feature(attribute=schemas.FeatureAttribute.IDENTIFIER),
        )

    rec = schemas.PIIRecord(
        name=[{"given": ["John"], "family": "Shepard"}],
        birthDate="1980-11-7",
        address=[{"line": ["1234 Silversun Strip"]}],
    )
    pat = models.Patient(
        data={
            "name": [{"given": ["John"], "family": "Sheperd"}],
            "birthDate": "1970-06-07",
            "address": [{"line": ["asdfghjeki"]}],
        }
    )
    log_odds = {
        schemas.FeatureAttribute.FIRST_NAME.value: 4.0,
        schemas.FeatureAttribute.LAST_NAME.value: 6.5,
        schemas.FeatureAttribute.BIRTHDATE.value: 9.8,
        schemas.FeatureAttribute.ADDRESS.value: 3.7,
    }

    assert (
        matchers.compare_probabilistic_fuzzy_match(
            rec, pat, schemas.Feature(attribute=schemas.FeatureAttribute.FIRST_NAME), log_odds=log_odds
        )
        == 4.0
    )

    assert (
        round(
            matchers.compare_probabilistic_fuzzy_match(
                rec, pat, schemas.Feature(attribute=schemas.FeatureAttribute.LAST_NAME), log_odds=log_odds
            ),
            3,
        )
        == 6.129
    )

    assert (
        round(
            matchers.compare_probabilistic_fuzzy_match(
                rec, pat, schemas.Feature(attribute=schemas.FeatureAttribute.BIRTHDATE), log_odds=log_odds
            ),
            3,
        )
        == 7.859
    )

    assert (
        round(
            matchers.compare_probabilistic_fuzzy_match(
                rec, pat, schemas.Feature(attribute=schemas.FeatureAttribute.ADDRESS), log_odds=log_odds
            ),
            3,
        )
        == 0.0
    )

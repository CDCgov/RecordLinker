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


class TestFeatureFunc:
    def test_correct_signatures(self):
        for rule in matchers.FeatureFunc:
            fn = utils.str_to_callable(rule.value)
            assert callable(fn)
            signature = inspect.signature(fn)
            params = list(signature.parameters.values())
            assert len(params) == 5
            assert params[0].annotation == schemas.PIIRecord
            assert params[1].annotation == models.Patient
            assert params[2].annotation == schemas.Feature
            assert params[3].annotation is float
            assert params[4].annotation == typing.Any
            assert signature.return_annotation is float


def test_compare_probabilistic_exact_match():
    rec = schemas.PIIRecord(
        name=[{"given": ["John", "T"], "family": "Shepard"}],
        birthDate="1980-11-7",
    )
    pat = models.Patient(
        data={
            "name": [{"given": ["John"], "family": "Shepard"}],
            "birthDate": "1970-06-07",
        }
    )

    assert (
        matchers.compare_probabilistic_exact_match(
            rec, pat, schemas.Feature(attribute=schemas.FeatureAttribute.FIRST_NAME), 4.0
        )
        == 4.0
    )

    assert (
        matchers.compare_probabilistic_exact_match(
            rec, pat, schemas.Feature(attribute=schemas.FeatureAttribute.LAST_NAME), 6.5
        )
        == 6.5
    )

    assert (
        matchers.compare_probabilistic_exact_match(
            rec, pat, schemas.Feature(attribute=schemas.FeatureAttribute.BIRTHDATE), 9.8
        )
        == 0.0
    )


def test_compare_probabilistic_fuzzy_match():
    with pytest.raises(AssertionError):
        matchers.compare_probabilistic_fuzzy_match(
            schemas.PIIRecord(),
            models.Patient(),
            schemas.Feature(attribute=schemas.FeatureAttribute.IDENTIFIER),
            0.0
        )

    rec = schemas.PIIRecord(
        name=[{"given": ["John"], "family": "Shepard"}],
        birthDate="1980-11-7",
        address=[{"line": ["1234 Silversun Sq"]}],
    )
    pat = models.Patient(
        data={
            "name": [{"given": ["John"], "family": "Sheperd"}],
            "birthDate": "1970-06-07",
            "address": [{"line": ["1234 Silversun Square"]}],
        }
    )

    assert (
        matchers.compare_probabilistic_fuzzy_match(
            rec, pat, schemas.Feature(attribute=schemas.FeatureAttribute.FIRST_NAME), 4.0,
            fuzzy_match_measure="JaroWinkler", fuzzy_match_threshold=0.9
        )
        == 4.0
    )

    assert (
        round(
            matchers.compare_probabilistic_fuzzy_match(
                rec, pat, schemas.Feature(attribute=schemas.FeatureAttribute.LAST_NAME), 6.5,
                fuzzy_match_measure="JaroWinkler", fuzzy_match_threshold=0.9
            ),
            3,
        )
        == 6.129
    )

    assert (
        round(
            matchers.compare_probabilistic_fuzzy_match(
                rec, pat, schemas.Feature(attribute=schemas.FeatureAttribute.BIRTHDATE), 9.8,
                fuzzy_match_measure="JaroWinkler", fuzzy_match_threshold=0.95
            ),
            3,
        )
        == 0.0
    )

    assert (
        round(
            matchers.compare_probabilistic_fuzzy_match(
                rec, pat, schemas.Feature(attribute=schemas.FeatureAttribute.ADDRESS), 3.7,
                fuzzy_match_measure="JaroWinkler", fuzzy_match_threshold=0.9
            ),
            3,
        )
        == 3.544
    )

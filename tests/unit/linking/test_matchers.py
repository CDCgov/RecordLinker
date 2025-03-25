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


class TestFeatureFunc:
    def test_correct_signatures(self):
        for rule in matchers.FeatureFunc:
            fn = rule.callable()
            assert callable(fn)
            signature = inspect.signature(fn)
            params = list(signature.parameters.values())
            assert len(params) >= 6
            assert params[0].annotation == schemas.PIIRecord
            assert params[1].annotation == models.Patient
            assert params[2].annotation == schemas.Feature
            assert params[3].annotation is float
            assert params[4].annotation is float
            assert params[-1].annotation == typing.Any
            assert signature.return_annotation == tuple[float, bool]


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

    assert matchers.compare_probabilistic_exact_match(
        rec,
        pat,
        schemas.Feature(attribute=schemas.FeatureAttribute.FIRST_NAME),
        4.0,
        0.5,
    ) == (4.0, False)

    assert matchers.compare_probabilistic_exact_match(
        rec,
        pat,
        schemas.Feature(attribute=schemas.FeatureAttribute.LAST_NAME),
        6.5,
        0.5,
    ) == (6.5, False)

    assert matchers.compare_probabilistic_exact_match(
        rec,
        pat,
        schemas.Feature(attribute=schemas.FeatureAttribute.BIRTHDATE),
        9.8,
        0.5,
    ) == (0.0, False)

    # Now do a missing case
    rec = schemas.PIIRecord(
        name=[{"given": ["John", "T"], "family": "Shepard"}],
    )
    assert matchers.compare_probabilistic_exact_match(
        rec,
        pat,
        schemas.Feature(attribute=schemas.FeatureAttribute.BIRTHDATE),
        9.8,
        0.5,
    ) == (4.9, True)


def test_compare_probabilistic_fuzzy_match():
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

    result, is_missing = matchers.compare_probabilistic_fuzzy_match(
        rec,
        pat,
        schemas.Feature(attribute=schemas.FeatureAttribute.FIRST_NAME),
        4.0,
        0.5,
        fuzzy_match_measure="JaroWinkler",
        fuzzy_match_threshold=0.9,
    )
    assert result == 4.0
    assert not is_missing

    result, is_missing = matchers.compare_probabilistic_fuzzy_match(
        rec,
        pat,
        schemas.Feature(attribute=schemas.FeatureAttribute.LAST_NAME),
        6.5,
        0.5,
        fuzzy_match_measure="JaroWinkler",
        fuzzy_match_threshold=0.9,
    )
    assert pytest.approx(result, 0.001) == 6.129
    assert not is_missing

    result, is_missing = matchers.compare_probabilistic_fuzzy_match(
        rec,
        pat,
        schemas.Feature(attribute=schemas.FeatureAttribute.BIRTHDATE),
        9.8,
        0.5,
        fuzzy_match_measure="JaroWinkler",
        fuzzy_match_threshold=0.95,
    )
    assert result == 0.0
    assert not is_missing

    result, is_missing = matchers.compare_probabilistic_fuzzy_match(
        rec,
        pat,
        schemas.Feature(attribute=schemas.FeatureAttribute.ADDRESS),
        3.7,
        0.5,
        fuzzy_match_measure="JaroWinkler",
        fuzzy_match_threshold=0.9,
    )
    assert pytest.approx(result, 0.001) == 3.544
    assert not is_missing

    # Test a missing field case
    rec = schemas.PIIRecord(
        name=[{"given": [], "family": "Shepard"}],
        birthDate="1980-11-7",
        address=[{"line": ["1234 Silversun Strip"]}],
    )
    result, is_missing = matchers.compare_probabilistic_fuzzy_match(
        rec,
        pat,
        schemas.Feature(attribute=schemas.FeatureAttribute.FIRST_NAME),
        4.0,
        0.5,
        fuzzy_match_measure="JaroWinkler",
        fuzzy_match_threshold=0.9,
    )
    assert result == 2.0
    assert is_missing

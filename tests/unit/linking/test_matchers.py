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


def test_exact_match_any():
    record = schemas.PIIRecord(
        name=[{"given": ["John", "Michael"], "family": "Smith"}, {"family": "Harrison"}],
        birthDate="Jan 1 1980",
    )
    pat1 = models.Patient(
        data={"name": [{"given": ["John", "Michael"], "family": "Doe"}], "birthDate": "1980-01-01"}
    )
    pat2 = models.Patient(data={"name": [{"given": ["Michael"], "family": "Smith"}], "sex": "male"})
    pat3 = models.Patient(data={"name": [{"family": "Smith"}, {"family": "Williams"}]})

    assert matchers.exact_match_any(record, pat1, schemas.Feature.GIVEN_NAME)
    assert matchers.exact_match_any(record, pat1, schemas.Feature.FIRST_NAME)
    assert not matchers.exact_match_any(record, pat1, schemas.Feature.LAST_NAME)
    assert matchers.exact_match_any(record, pat1, schemas.Feature.BIRTHDATE)
    assert not matchers.exact_match_any(record, pat1, schemas.Feature.ZIP)

    assert matchers.exact_match_any(record, pat2, schemas.Feature.GIVEN_NAME)
    assert not matchers.exact_match_any(record, pat2, schemas.Feature.FIRST_NAME)
    assert matchers.exact_match_any(record, pat2, schemas.Feature.LAST_NAME)
    assert not matchers.exact_match_any(record, pat2, schemas.Feature.SEX)
    assert not matchers.exact_match_any(record, pat1, schemas.Feature.ZIP)

    assert not matchers.exact_match_any(record, pat3, schemas.Feature.GIVEN_NAME)
    assert not matchers.exact_match_any(record, pat3, schemas.Feature.FIRST_NAME)
    assert matchers.exact_match_any(record, pat3, schemas.Feature.LAST_NAME)
    assert not matchers.exact_match_any(record, pat3, schemas.Feature.BIRTHDATE)

    with pytest.raises(ValueError):
        matchers.exact_match_any(record, pat1, "unknown")


def test_exact_match_all():
    record = schemas.PIIRecord(
        name=[{"given": ["John"], "family": "Smith"}, {"family": "Harrison"}],
        birthDate="December 31, 1999",
    )
    pat1 = models.Patient(
        data={"name": [{"given": ["John", "Michael"], "family": "Doe"}], "birthDate": "1999-12-31"}
    )
    pat2 = models.Patient(
        data={
            "name": [{"given": ["John"], "family": "Smith"}],
            "sex": "male",
            "address": [{"zipcode": "12345"}],
        },
    )
    pat3 = models.Patient(data={"name": [{"family": "Smith"}, {"family": "Harrison"}]})

    assert not matchers.exact_match_all(record, pat1, schemas.Feature.GIVEN_NAME)
    assert matchers.exact_match_all(record, pat1, schemas.Feature.FIRST_NAME)
    assert not matchers.exact_match_all(record, pat1, schemas.Feature.LAST_NAME)
    assert matchers.exact_match_all(record, pat1, schemas.Feature.BIRTHDATE)
    assert not matchers.exact_match_all(record, pat1, schemas.Feature.ZIP)

    assert matchers.exact_match_all(record, pat2, schemas.Feature.GIVEN_NAME)
    assert matchers.exact_match_all(record, pat2, schemas.Feature.FIRST_NAME)
    assert not matchers.exact_match_all(record, pat2, schemas.Feature.LAST_NAME)
    assert not matchers.exact_match_all(record, pat2, schemas.Feature.SEX)
    assert not matchers.exact_match_all(record, pat2, schemas.Feature.ZIP)

    assert not matchers.exact_match_all(record, pat3, schemas.Feature.FIRST_NAME)
    assert matchers.exact_match_all(record, pat3, schemas.Feature.LAST_NAME)
    assert not matchers.exact_match_all(record, pat3, schemas.Feature.BIRTHDATE)

    with pytest.raises(ValueError):
        matchers.exact_match_all(record, pat1, "unknown")


def test_fuzzy_match():
    record = schemas.PIIRecord(
        name=[{"given": ["John"], "family": "Smith"}, {"family": "Harrison"}],
        birthDate="1980-01-01",
    )
    pat1 = models.Patient(
        data={"name": [{"given": ["Jon", "Mike"], "family": "Doe"}], "birthDate": "Jan 1 1980"}
    )
    pat2 = models.Patient(data={"name": [{"given": ["Michael"], "family": "Smtih"}], "sex": "male"})
    pat3 = models.Patient(data={"name": [{"family": "Smyth"}, {"family": "Williams"}]})

    assert matchers.fuzzy_match(record, pat1, schemas.Feature.FIRST_NAME)
    assert not matchers.fuzzy_match(record, pat1, schemas.Feature.LAST_NAME)

    assert not matchers.fuzzy_match(record, pat2, schemas.Feature.FIRST_NAME)
    assert matchers.fuzzy_match(record, pat2, schemas.Feature.LAST_NAME)

    assert not matchers.fuzzy_match(record, pat3, schemas.Feature.FIRST_NAME)
    assert matchers.fuzzy_match(record, pat3, schemas.Feature.LAST_NAME)

    with pytest.raises(ValueError):
        matchers.fuzzy_match(record, pat1, "first_name")


def test_probabilistic_fuzzy_match():
    with pytest.raises(ValueError):
        matchers.probabilistic_fuzzy_match(
            schemas.PIIRecord(),
            models.Patient(),
            schemas.Feature.MRN,
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
        schemas.Feature.FIRST_NAME.value: 4.0,
        schemas.Feature.LAST_NAME.value: 6.5,
        schemas.Feature.BIRTHDATE.value: 9.8,
        schemas.Feature.ADDRESS.value: 3.7,
    }

    assert (
        matchers.probabilistic_fuzzy_match(
            rec, pat, schemas.Feature.FIRST_NAME, log_odds=log_odds
        )
        == 4.0
    )

    assert (
        round(
            matchers.probabilistic_fuzzy_match(
                rec, pat, schemas.Feature.LAST_NAME, log_odds=log_odds
            ),
            3,
        )
        == 6.129
    )

    assert (
        round(
            matchers.probabilistic_fuzzy_match(
                rec, pat, schemas.Feature.BIRTHDATE, log_odds=log_odds
            ),
            3,
        )
        == 7.859
    )

    assert (
        round(
            matchers.probabilistic_fuzzy_match(
                rec, pat, schemas.Feature.ADDRESS, log_odds=log_odds
            ),
            3,
        )
        == 0.0
    )

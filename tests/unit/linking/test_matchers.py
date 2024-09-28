"""
unit.linking.test_matchers
~~~~~~~~~~~~~~~~~~

This module contains unit tests for the :mod:`~recordlinker.linking.matchers` module.
"""

import pytest

from recordlinker import models
from recordlinker.linking import matchers


def test_feature_match_any():
    record = models.PIIRecord(
        name=[{"given": ["John"], "family": "Smith"}, {"family": "Harrison"}],
        birthDate="1980-01-01",
    )
    pat1 = models.Patient(
        data={"name": [{"given": ["John", "Michael"], "family": "Doe"}], "birthDate": "Jan 1 1980"}
    )
    pat2 = models.Patient(data={"name": [{"given": ["Michael"], "family": "Smith"}], "sex": "male"})
    pat3 = models.Patient(data={"name": [{"family": "Smith"}, {"family": "Williams"}]})

    assert matchers.feature_match_any(record, pat1, models.Feature.FIRST_NAME)
    assert not matchers.feature_match_any(record, pat1, models.Feature.LAST_NAME)
    assert matchers.feature_match_any(record, pat1, models.Feature.BIRTHDATE)
    assert not matchers.feature_match_any(record, pat1, models.Feature.ZIPCODE)

    assert not matchers.feature_match_any(record, pat2, models.Feature.FIRST_NAME)
    assert matchers.feature_match_any(record, pat2, models.Feature.LAST_NAME)
    assert not matchers.feature_match_any(record, pat2, models.Feature.SEX)
    assert not matchers.feature_match_any(record, pat1, models.Feature.ZIPCODE)

    assert not matchers.feature_match_any(record, pat3, models.Feature.FIRST_NAME)
    assert matchers.feature_match_any(record, pat3, models.Feature.LAST_NAME)
    assert not matchers.feature_match_any(record, pat3, models.Feature.BIRTHDATE)

    with pytest.raises(ValueError):
        matchers.feature_match_any(record, pat1, "unknown")


def test_feature_match_exact():
    record = models.PIIRecord(
        name=[{"given": ["John"], "family": "Smith"}, {"family": "Harrison"}],
        birthDate="1980-01-01",
    )
    pat1 = models.Patient(
        data={"name": [{"given": ["John", "Michael"], "family": "Doe"}], "birthDate": "Jan 1 1980"}
    )
    pat2 = models.Patient(
        data={
            "name": [{"given": ["John"], "family": "Smith"}],
            "sex": "male",
            "address": [{"zipcode": "12345"}],
        },
    )
    pat3 = models.Patient(data={"name": [{"family": "Smith"}, {"family": "Harrison"}]})

    assert not matchers.feature_match_exact(record, pat1, models.Feature.FIRST_NAME)
    assert not matchers.feature_match_exact(record, pat1, models.Feature.LAST_NAME)
    assert matchers.feature_match_exact(record, pat1, models.Feature.BIRTHDATE)
    assert not matchers.feature_match_exact(record, pat1, models.Feature.ZIPCODE)

    assert matchers.feature_match_exact(record, pat2, models.Feature.FIRST_NAME)
    assert not matchers.feature_match_exact(record, pat2, models.Feature.LAST_NAME)
    assert not matchers.feature_match_exact(record, pat2, models.Feature.SEX)
    assert not matchers.feature_match_exact(record, pat2, models.Feature.ZIPCODE)

    assert not matchers.feature_match_exact(record, pat3, models.Feature.FIRST_NAME)
    assert matchers.feature_match_exact(record, pat3, models.Feature.LAST_NAME)
    assert not matchers.feature_match_exact(record, pat3, models.Feature.BIRTHDATE)

    with pytest.raises(ValueError):
        matchers.feature_match_exact(record, pat1, "unknown")


def test_feature_match_fuzzy_string():
    record = models.PIIRecord(
        name=[{"given": ["John"], "family": "Smith"}, {"family": "Harrison"}],
        birthDate="1980-01-01",
    )
    pat1 = models.Patient(
        data={"name": [{"given": ["Jon", "Mike"], "family": "Doe"}], "birthDate": "Jan 1 1980"}
    )
    pat2 = models.Patient(data={"name": [{"given": ["Michael"], "family": "Smtih"}], "sex": "male"})
    pat3 = models.Patient(data={"name": [{"family": "Smyth"}, {"family": "Williams"}]})

    assert matchers.feature_match_fuzzy_string(record, pat1, models.Feature.FIRST_NAME)
    assert not matchers.feature_match_fuzzy_string(record, pat1, models.Feature.LAST_NAME)

    assert not matchers.feature_match_fuzzy_string(record, pat2, models.Feature.FIRST_NAME)
    assert matchers.feature_match_fuzzy_string(record, pat2, models.Feature.LAST_NAME)

    assert not matchers.feature_match_fuzzy_string(record, pat3, models.Feature.FIRST_NAME)
    assert matchers.feature_match_fuzzy_string(record, pat3, models.Feature.LAST_NAME)

    with pytest.raises(ValueError):
        matchers.feature_match_fuzzy_string(record, pat1, "first_name")


def test_feature_match_log_odds_fuzzy_compare():
    with pytest.raises(ValueError):
        matchers.feature_match_log_odds_fuzzy_compare(
            models.PIIRecord(),
            models.Patient(),
            models.Feature.MRN,
        )

    rec = models.PIIRecord(
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
        models.Feature.FIRST_NAME.value: 4.0,
        models.Feature.LAST_NAME.value: 6.5,
        models.Feature.BIRTHDATE.value: 9.8,
        models.Feature.ADDRESS.value: 3.7,
    }

    assert (
        matchers.feature_match_log_odds_fuzzy_compare(
            rec, pat, models.Feature.FIRST_NAME, log_odds=log_odds
        )
        == 4.0
    )

    assert (
        round(
            matchers.feature_match_log_odds_fuzzy_compare(
                rec, pat, models.Feature.LAST_NAME, log_odds=log_odds
            ),
            3,
        )
        == 6.129
    )

    assert (
        round(
            matchers.feature_match_log_odds_fuzzy_compare(
                rec, pat, models.Feature.BIRTHDATE, log_odds=log_odds
            ),
            3,
        )
        == 7.859
    )

    assert (
        round(
            matchers.feature_match_log_odds_fuzzy_compare(
                rec, pat, models.Feature.ADDRESS, log_odds=log_odds
            ),
            3,
        )
        == 0.0
    )

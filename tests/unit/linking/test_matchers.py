"""
unit.linking.test_matchers
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains unit tests for the :mod:`~recordlinker.linking.matchers` module.
"""

import inspect
import typing

from recordlinker import models
from recordlinker import schemas
from recordlinker.linking import matchers


class TestFeatureFunc:
    def test_correct_signatures(self):
        for rule in matchers.FeatureFunc:
            signature = inspect.signature(rule.callable())
            params = list(signature.parameters.values())
            assert len(params) >= 6
            assert params[0].annotation == schemas.PIIRecord
            assert params[1].annotation == schemas.PIIRecord
            assert params[2].annotation == schemas.Feature
            assert params[3].annotation is float
            assert params[4].annotation is float
            assert params[-1].annotation == typing.Any
            assert signature.return_annotation == tuple[float, bool]

    def test_callable(self):
        assert (
            matchers.FeatureFunc["COMPARE_PROBABILISTIC_EXACT_MATCH"].callable()
            == matchers.compare_probabilistic_exact_match
        )
        assert (
            matchers.FeatureFunc["COMPARE_PROBABILISTIC_FUZZY_MATCH"].callable()
            == matchers.compare_probabilistic_fuzzy_match
        )

    def test_str(self):
        assert (
            str(matchers.FeatureFunc["COMPARE_PROBABILISTIC_EXACT_MATCH"])
            == "COMPARE_PROBABILISTIC_EXACT_MATCH"
        )
        assert (
            str(matchers.FeatureFunc["COMPARE_PROBABILISTIC_FUZZY_MATCH"])
            == "COMPARE_PROBABILISTIC_FUZZY_MATCH"
        )


def test_compare_probabilistic_exact_match():
    missing_points_proportion = 0.5

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
        schemas.PIIRecord.from_patient(pat),
        schemas.Feature(attribute=schemas.FeatureAttribute.FIRST_NAME),
        4.0,
        missing_points_proportion,
    ) == (4.0, False)

    assert matchers.compare_probabilistic_exact_match(
        rec,
        schemas.PIIRecord.from_patient(pat),
        schemas.Feature(attribute=schemas.FeatureAttribute.LAST_NAME),
        6.5,
        missing_points_proportion,
    ) == (6.5, False)

    assert matchers.compare_probabilistic_exact_match(
        rec,
        schemas.PIIRecord.from_patient(pat),
        schemas.Feature(attribute=schemas.FeatureAttribute.BIRTHDATE),
        9.8,
        missing_points_proportion,
    ) == (0.0, False)

    # Now do a missing case
    rec = schemas.PIIRecord(
        name=[{"given": ["John", "T"], "family": "Shepard"}],
    )
    assert matchers.compare_probabilistic_exact_match(
        rec,
        schemas.PIIRecord.from_patient(pat),
        schemas.Feature(attribute=schemas.FeatureAttribute.BIRTHDATE),
        9.8,
        missing_points_proportion,
    ) == (4.9, True)

    # Suffix comparison cases
    rec = schemas.PIIRecord(
        name=[{"given": ["Joel"], "family": "Miller", "suffix": ["Senior"]}],
    )
    pat = models.Patient(
        data={
            "name": [{"given": ["Joel"], "family": "Miller"}],
            "birthDate": "1970-06-07",
        }
    )
    assert matchers.compare_probabilistic_exact_match(
        rec,
        schemas.PIIRecord.from_patient(pat),
        schemas.Feature(attribute=schemas.FeatureAttribute.FIRST_NAME),
        6.85,
        missing_points_proportion,
    ) == (0.0, False)

    pat = models.Patient(
        data={
            "name": [{"given": ["Joel"], "family": "Miller", "suffix": ["Sr"]}],
            "birthDate": "1970-06-07",
        }
    )
    assert matchers.compare_probabilistic_exact_match(
        rec,
        schemas.PIIRecord.from_patient(pat),
        schemas.Feature(attribute=schemas.FeatureAttribute.FIRST_NAME),
        6.85,
        missing_points_proportion,
    ) == (6.85, False)


def test_compare_probabilistic_fuzzy_match():
    missing_points_proportion = 0.5

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

    assert matchers.compare_probabilistic_fuzzy_match(
        rec,
        schemas.PIIRecord.from_patient(pat),
        schemas.Feature(attribute=schemas.FeatureAttribute.FIRST_NAME),
        4.0,
        missing_points_proportion,
        fuzzy_match_measure="JaroWinkler",
        fuzzy_match_threshold=0.7,
    ) == (4.0, False)

    result = matchers.compare_probabilistic_fuzzy_match(
        rec,
        schemas.PIIRecord.from_patient(pat),
        schemas.Feature(attribute=schemas.FeatureAttribute.LAST_NAME),
        6.5,
        missing_points_proportion,
        fuzzy_match_measure="JaroWinkler",
        fuzzy_match_threshold=0.7,
    )
    assert round(result[0], 3) == 6.129
    assert not result[1]

    result = matchers.compare_probabilistic_fuzzy_match(
        rec,
        schemas.PIIRecord.from_patient(pat),
        schemas.Feature(attribute=schemas.FeatureAttribute.BIRTHDATE),
        9.8,
        missing_points_proportion,
        fuzzy_match_measure="JaroWinkler",
        fuzzy_match_threshold=0.7,
    )
    assert round(result[0], 3) == 7.859
    assert not result[1]

    result = matchers.compare_probabilistic_fuzzy_match(
        rec,
        schemas.PIIRecord.from_patient(pat),
        schemas.Feature(attribute=schemas.FeatureAttribute.ADDRESS),
        3.7,
        missing_points_proportion,
        fuzzy_match_measure="JaroWinkler",
        fuzzy_match_threshold=0.7,
    )
    assert round(result[0], 3) == 0.0
    assert not result[1]

    # Test a missing field case
    rec = schemas.PIIRecord(
        name=[{"given": [], "family": "Shepard"}],
        birthDate="1980-11-7",
        address=[{"line": ["1234 Silversun Strip"]}],
    )
    result = matchers.compare_probabilistic_fuzzy_match(
        rec,
        schemas.PIIRecord.from_patient(pat),
        schemas.Feature(attribute=schemas.FeatureAttribute.FIRST_NAME),
        4.0,
        missing_points_proportion,
        fuzzy_match_measure="JaroWinkler",
        fuzzy_match_threshold=0.7,
    )
    assert round(result[0], 3) == 2.0
    assert result[1]

    # Test fuzzy comparisons with suffix
    # Test 1: Same name, spelled correctly, one with suffix, other without
    rec = schemas.PIIRecord(
        name=[{"given": ["Joel"], "family": "Miller", "suffix": ["Senior"]}],
    )
    pat = models.Patient(
        data={
            "name": [{"given": ["Joel"], "family": "Miller"}],
            "birthDate": "1970-06-07",
        }
    )
    result = matchers.compare_probabilistic_fuzzy_match(
        rec,
        schemas.PIIRecord.from_patient(pat),
        schemas.Feature(attribute=schemas.FeatureAttribute.FIRST_NAME),
        6.85,
        missing_points_proportion,
        fuzzy_match_measure="JaroWinkler",
        fuzzy_match_threshold=0.7,
    )
    assert round(result[0], 3) == 6.089

    # Test 2: Same name, spelled incorrectly, one with suffix, other without
    pat = models.Patient(
        data={
            "name": [{"given": ["Jeol"], "family": "Miller"}],
            "birthDate": "1970-06-07",
        }
    )
    result = matchers.compare_probabilistic_fuzzy_match(
        rec,
        schemas.PIIRecord.from_patient(pat),
        schemas.Feature(attribute=schemas.FeatureAttribute.FIRST_NAME),
        6.85,
        missing_points_proportion,
        fuzzy_match_measure="JaroWinkler",
        fuzzy_match_threshold=0.7,
    )
    assert round(result[0], 3) == 5.137

    # Test 3: Same name, spelled correctly, both with suffixes
    pat = models.Patient(
        data={
            "name": [{"given": ["Joel"], "family": "Miller", "suffix": ["Sr"]}],
            "birthDate": "1970-06-07",
        }
    )
    result = matchers.compare_probabilistic_fuzzy_match(
        rec,
        schemas.PIIRecord.from_patient(pat),
        schemas.Feature(attribute=schemas.FeatureAttribute.FIRST_NAME),
        6.85,
        missing_points_proportion,
        fuzzy_match_measure="JaroWinkler",
        fuzzy_match_threshold=0.7,
    )
    assert round(result[0], 3) == 6.850

    # Test 4: Different name, each with suffix
    pat = models.Patient(
        data={
            "name": [{"given": ["Ellie"], "family": "Williams", "suffix": ["Jr"]}],
            "birthDate": "2019-04-11",
        }
    )
    result = matchers.compare_probabilistic_fuzzy_match(
        rec,
        schemas.PIIRecord.from_patient(pat),
        schemas.Feature(attribute=schemas.FeatureAttribute.FIRST_NAME),
        6.85,
        missing_points_proportion,
        fuzzy_match_measure="JaroWinkler",
        fuzzy_match_threshold=0.7,
    )
    assert round(result[0], 3) == 0.0
    

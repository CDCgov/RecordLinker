"""
unit.schemas.test_algorithm.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.schemas.algorithm module.
"""

import pydantic
import pytest

from recordlinker.schemas.algorithm import Algorithm
from recordlinker.schemas.algorithm import AlgorithmPass
from recordlinker.schemas.algorithm import LogOdd
from recordlinker.schemas.algorithm import SkipValue


class TestAlgorithmPass:
    def test_validate_blocking_keys(self):
        keys = ["name", "birthDate"]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=keys,
                evaluators=[],
            )
        keys = ["LAST_NAME", "BIRTHDATE", "ZIP"]
        # write an assertion that no exception is raised
        AlgorithmPass(
            blocking_keys=keys,
            evaluators=[],
            possible_match_window=(0.75, 1.0),
        )

    def test_validate_possible_match_window(self):
        possible_match_window = (0.9, 0.75)
        evaluators = [
            {
                "feature": "LAST_NAME",
                "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH",
            }
        ]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=["LAST_NAME", "BIRTHDATE"],
                evaluators=evaluators,
                possible_match_window=possible_match_window
            )

        possible_match_window = (0.75, 0.9)
        AlgorithmPass(
            blocking_keys=["LAST_NAME", "BIRTHDATE"],
            evaluators=evaluators,
            possible_match_window=possible_match_window
        )

        possible_match_window = (0.9, 0.9)
        AlgorithmPass(
            blocking_keys=["LAST_NAME", "BIRTHDATE"],
            evaluators=evaluators,
            possible_match_window=possible_match_window
        )

    def test_validate_evaluators(self):
        # Tests non-existent / invalid feature name
        evaluators = [
            {"feature": "invalid", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"}
        ]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=evaluators,
                possible_match_window=(0.75, 1.0),
            )
        
        # Tests invalid evaluation functions
        evaluators = [
            {"feature": "LAST_NAME", "func": "UNKNOWN"}
        ]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=evaluators,
            )
        
        # Correct behavior
        evaluators = [{"feature": "LAST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"}]
        # write an assertion that no exception is raised
        AlgorithmPass(
            blocking_keys=[],
            evaluators=evaluators,
            possible_match_window=(0.75, 1.0),
        )

        evaluators = [{"feature": "FIRST_NAME:DL", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"}]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=evaluators,
                possible_match_window=(0.75, 1.0),
            )

    def test_default_label(self):
        apass = AlgorithmPass(
            blocking_keys=[],
            evaluators=[
                {"feature": "LAST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"}
            ],
            possible_match_window=[0.8, 0.9]
        )
        assert apass.label == "BLOCK_MATCH_last_name"
        apass = AlgorithmPass(
            blocking_keys=["ADDRESS"],
            evaluators=[
                {"feature": "LAST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"},
                {"feature": "FIRST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"},
            ],
            possible_match_window=[0.8, 0.9]
        )
        assert apass.label == "BLOCK_address_MATCH_last_name_first_name"
        apass = AlgorithmPass(
            label="custom-label",
            blocking_keys=[],
            evaluators=[
                {"feature": "LAST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"}
            ],
            possible_match_window=[0.8, 0.9]
        )
        assert apass.label == "custom-label"


class TestLogOdd:
    def test_invalid_feature(self):
        with pytest.raises(pydantic.ValidationError):
            LogOdd(feature="invalid", value=1.0)

    def test_value_less_than_zero(self):
        with pytest.raises(pydantic.ValidationError):
            LogOdd(feature="FIRST_NAME", value=-1.0)


class TestSkipValue:
    def test_invalid_feature(self):
        with pytest.raises(pydantic.ValidationError):
            SkipValue(feature="invalid", values=["X"])

    def test_missing_values(self):
        with pytest.raises(pydantic.ValidationError):
            SkipValue(feature="FIRST_NAME", values=[])

    def test_astrisk_feature(self):
        skip_value = SkipValue(feature="*", values=["X"])
        assert skip_value.feature == "*"
        assert skip_value.values == ["X"]

    def test_values(self):
        skip_value = SkipValue(feature="EMAIL", values=["X", "Y * Z"])
        assert skip_value.feature == "EMAIL"
        assert skip_value.values == ["X", "Y * Z"]


class TestAlgorithm:
    def test_validate_pass_labels(self):
        with pytest.raises(pydantic.ValidationError):
            Algorithm(
                label="label",
                max_missing_allowed_proportion=0.5,
                missing_field_points_proportion=0.5,
                passes=[
                    AlgorithmPass(
                        label="pass",
                        blocking_keys=[],
                        evaluators=[],
                        possible_match_window=[0.8, 0.9]
                    ),
                    AlgorithmPass(
                        label="pass",
                        blocking_keys=[],
                        evaluators=[],
                        possible_match_window=[0.8, 0.9]
                    ),
                ],
            )
        Algorithm(
            label="label",
            max_missing_allowed_proportion=0.5,
            missing_field_points_proportion=0.5,
            passes=[
                AlgorithmPass(
                    label="pass1",
                    blocking_keys=[],
                    evaluators=[],
                    possible_match_window=[0.8, 0.9]
                ),
                AlgorithmPass(
                    label="pass2",
                    blocking_keys=[],
                    evaluators=[],
                    possible_match_window=[0.8, 0.9]
                ),
            ],
        )

    def test_validate_log_odds_defined(self):
        with pytest.raises(pydantic.ValidationError):
            Algorithm(
                label="test",
                max_missing_allowed_proportion=0.5,
                missing_field_points_proportion=0.5,
                passes=[
                    AlgorithmPass(
                        blocking_keys=["BIRTHDATE"],
                        evaluators=[],
                        possible_match_window=(0.75, 1.0),
                    )
                ],
            )
        with pytest.raises(pydantic.ValidationError):
            Algorithm(
                label="test",
                max_missing_allowed_proportion=0.5,
                missing_field_points_proportion=0.5,
                passes=[
                    AlgorithmPass(
                        blocking_keys=[],
                        evaluators=[
                            {"feature": "FIRST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"}
                        ],
                        possible_match_window=(0.75, 1.0),
                    )
                ],
            )
        Algorithm(
            label="test",
            max_missing_allowed_proportion=0.5,
            missing_field_points_proportion=0.5,
            algorithm_context={
                "log_odds": [
                    {"feature": "FIRST_NAME", "value": 7},
                    {"feature": "BIRTHDATE", "value": 10},
                ]
            },
            passes=[
                AlgorithmPass(
                    blocking_keys=["BIRTHDATE"],
                    evaluators=[
                        {"feature": "FIRST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"}
                    ],
                    possible_match_window=(0.75, 1.0),
                )
            ],
        )

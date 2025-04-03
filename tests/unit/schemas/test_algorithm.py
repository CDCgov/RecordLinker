"""
unit.schemas.test_algorithm.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.schemas.algorithm module.
"""

import pydantic
import pytest

from recordlinker.schemas.algorithm import Algorithm
from recordlinker.schemas.algorithm import AlgorithmPass


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
        )

    def test_validate_evaluators(self):
        evaluators = [
            {"feature": "name", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"}
        ]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=evaluators,
            )
        evaluators = [
            {"feature": "LAST_NAME", "func": "UNKNOWN"}
        ]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=evaluators,
            )
        evaluators = [
            {"feature": "LAST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"}
        ]
        # write an assertion that no exception is raised
        AlgorithmPass(
            blocking_keys=[],
            evaluators=evaluators,
        )

        evaluators = [
            {"feature": "FIRST_NAME:DL", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"}
        ]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=evaluators,
            )

    def test_kwargs(self):
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=[],
                cluster_ratio=0.5,
                kwargs={"invalid": "key"},
            )
        AlgorithmPass(
            blocking_keys=[],
            evaluators=[],
            kwargs={
                "similarity_measure": "JaroWinkler",
                "thresholds": {"CITY": 0.95, "ADDRESS": 0.98},
                "threshold": 0.9,
                "log_odds": {"CITY": 12.0, "ADDRESS": 15.0},
                "true_match_threshold": 0.8,
            },
        )


class TestAlgorithm:
    def test_validate_belongingness_ratio(self):
        belongingness_ratio = (0.9, 0.75)
        with pytest.raises(pydantic.ValidationError):
            Algorithm(
                label="label",
                belongingness_ratio=belongingness_ratio,
                max_missing_allowed_proportion=0.5,
                missing_field_points_proportion=0.5,
                passes=[
                    AlgorithmPass(
                        blocking_keys=[],
                        evaluators=[],
                    )
                ],
            )
        belongingness_ratio = (0.75, 0.9)
        Algorithm(
            label="label",
            belongingness_ratio=belongingness_ratio,
            max_missing_allowed_proportion=0.5,
            missing_field_points_proportion=0.5,
            passes=[
                AlgorithmPass(
                    blocking_keys=[],
                    evaluators=[],
                )
            ],
        )
        belongingness_ratio = (0.9, 0.9)
        Algorithm(
            label="label",
            belongingness_ratio=belongingness_ratio,
            max_missing_allowed_proportion=0.5,
            missing_field_points_proportion=0.5,
            passes=[
                AlgorithmPass(
                    blocking_keys=[],
                    evaluators=[],
                )
            ],
        )

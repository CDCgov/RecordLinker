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

    def test_default_label(self):
        apass = AlgorithmPass(
            blocking_keys=[],
            evaluators=[
                {"feature": "LAST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"}
            ],
            rule="func:recordlinker.linking.matchers.rule_probabilistic_match",
        )
        assert apass.label == "BLOCK_MATCH_last_name"
        apass = AlgorithmPass(
            blocking_keys=["ADDRESS"],
            evaluators=[
                {"feature": "LAST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"},
                {"feature": "FIRST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"},
            ],
            rule="func:recordlinker.linking.matchers.rule_probabilistic_match",
        )
        assert apass.label == "BLOCK_address_MATCH_last_name_first_name"
        apass = AlgorithmPass(
            label="custom-label",
            blocking_keys=[],
            evaluators=[
                {"feature": "LAST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"},
            ],
            rule="func:recordlinker.linking.matchers.rule_probabilistic_match",
        )
        assert apass.label == "custom-label"


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

    def test_validate_pass_labels(self):
        with pytest.raises(pydantic.ValidationError):
            Algorithm(
                label="label",
                belongingness_ratio=(0.9, 0.9),
                max_missing_allowed_proportion=0.5,
                missing_field_points_proportion=0.5,
                passes=[
                    AlgorithmPass(
                        label="pass",
                        blocking_keys=[],
                        evaluators=[],
                        rule="func:recordlinker.linking.matchers.rule_probabilistic_match",
                    ),
                    AlgorithmPass(
                        label="pass",
                        blocking_keys=[],
                        evaluators=[],
                        rule="func:recordlinker.linking.matchers.rule_probabilistic_match",
                    )
                ],
            )
        Algorithm(
            label="label",
            belongingness_ratio=(0.9, 0.9),
            max_missing_allowed_proportion=0.5,
            missing_field_points_proportion=0.5,
            passes=[
                AlgorithmPass(
                    label="pass1",
                    blocking_keys=[],
                    evaluators=[],
                    rule="func:recordlinker.linking.matchers.rule_probabilistic_match",
                ),
                AlgorithmPass(
                    label="pass2",
                    blocking_keys=[],
                    evaluators=[],
                    rule="func:recordlinker.linking.matchers.rule_probabilistic_match",
                )
            ],
        )

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
                evaluators={},
                rule="func:recordlinker.linking.matchers.eval_perfect_match",
            )
        keys = ["LAST_NAME", "BIRTHDATE", "ZIP"]
        # write an assertion that no exception is raised
        AlgorithmPass(
            blocking_keys=keys,
            evaluators={},
            rule="func:recordlinker.linking.matchers.eval_perfect_match",
        )

    def test_validate_evaluators(self):
        evaluators = {"name": "func:recordlinker.linking.matchers.feature_match_any"}
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=evaluators,
                rule="func:recordlinker.linking.matchers.eval_perfect_match",
            )
        evaluators = {"LAST_NAME": "func:recordlinker.linking.matchers.unknown"}
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=evaluators,
                rule="func:recordlinker.linking.matchers.eval_perfect_match",
            )
        evaluators = {"LAST_NAME": "func:recordlinker.linking.matchers.eval_perfect_match"}
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=evaluators,
                rule="func:recordlinker.linking.matchers.eval_perfect_match",
            )
        evaluators = {"LAST_NAME": "func:recordlinker.linking.matchers.feature_match_any"}
        # write an assertion that no exception is raised
        AlgorithmPass(
            blocking_keys=[],
            evaluators=evaluators,
            rule="func:recordlinker.linking.matchers.eval_perfect_match",
        )

    def test_validate_rule(self):
        rule = "invalid.func"
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators={},
                rule=rule,
            )
        rule = "func:recordlinker.linking.matchers.feature_match_any"
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators={},
                rule=rule,
            )
        rule = "fn:recordlinker.linking.matchers.eval_perfect_match"
        AlgorithmPass(
            blocking_keys=[],
            evaluators={},
            rule=rule,
        )
        rule = "recordlinker.linking.matchers.eval_perfect_match"
        AlgorithmPass(
            blocking_keys=[],
            evaluators={},
            rule=rule,
        )


class TestAlgorithm:
    def test_validate_belongingness_ratio(self):
        belongingness_ratio=(0.9, 0.75)
        with pytest.raises(pydantic.ValidationError):
            Algorithm(
                label="label",
                belongingness_ratio=belongingness_ratio,
                passes=[
                    AlgorithmPass(
                        blocking_keys=[],
                        evaluators={},
                        rule="func:recordlinker.linking.matchers.eval_perfect_match",
                    )
                ]
            )
        belongingness_ratio=(0.75, 0.9)
        Algorithm(
            label="label",
            belongingness_ratio=belongingness_ratio,
            passes=[
                    AlgorithmPass(
                        blocking_keys=[],
                        evaluators={},
                        rule="func:recordlinker.linking.matchers.eval_perfect_match",
                    )
                ]
        )
        belongingness_ratio=(0.9, 0.9)
        Algorithm(
            label="label",
            belongingness_ratio=belongingness_ratio,
            passes=[
                    AlgorithmPass(
                        blocking_keys=[],
                        evaluators={},
                        rule="func:recordlinker.linking.matchers.eval_perfect_match",
                    )
                ]
        )


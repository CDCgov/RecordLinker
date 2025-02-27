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
                rule="func:recordlinker.linking.matchers.rule_probabilistic_sum",
            )
        keys = ["LAST_NAME", "BIRTHDATE", "ZIP"]
        # write an assertion that no exception is raised
        AlgorithmPass(
            blocking_keys=keys,
            evaluators=[],
            rule="func:recordlinker.linking.matchers.rule_probabilistic_sum",
            possible_match_window=(0.75, 1.0),
        )

    def test_validate_possible_match_window(self):
        possible_match_window = (0.9, 0.75)
        evaluators = [
            {
                "feature": "LAST_NAME",
                "func": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match",
            }
        ]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=["LAST_NAME", "BIRTHDATE"],
                evaluators=evaluators,
                rule="func:recordlinker.linking.matchers.rule_probabilistic_sum",
                possible_match_window=possible_match_window
            )

        possible_match_window = (0.75, 0.9)
        AlgorithmPass(
            blocking_keys=["LAST_NAME", "BIRTHDATE"],
            evaluators=evaluators,
            rule="func:recordlinker.linking.matchers.rule_probabilistic_sum",
            possible_match_window=possible_match_window
        )

        possible_match_window = (0.9, 0.9)
        AlgorithmPass(
            blocking_keys=["LAST_NAME", "BIRTHDATE"],
            evaluators=evaluators,
            rule="func:recordlinker.linking.matchers.rule_probabilistic_sum",
            possible_match_window=possible_match_window
        )

    def test_validate_evaluators(self):
        # Tests non-existent / invalid feature name
        evaluators = [
            {"feature": "name", "func": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match"}
        ]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=evaluators,
                rule="func:recordlinker.linking.matchers.rule_probabilistic_sum",
                possible_match_window=(0.75, 1.0),
            )
        
        # Tests invalid evaluation functions
        evaluators = [
            {"feature": "LAST_NAME", "func": "func:recordlinker.linking.matchers.unknown"}
        ]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=evaluators,
                rule="func:recordlinker.linking.matchers.rule_probabilistic_sum",
                possible_match_window=(0.75, 1.0),
            )
        
        # Tests using a match rule as a comparison function
        evaluators = [
            {
                "feature": "LAST_NAME",
                "func": "func:recordlinker.linking.matchers.rule_probabilistic_sum",
            }
        ]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=evaluators,
                rule="func:recordlinker.linking.matchers.rule_probabilistic_sum",
                possible_match_window=(0.75, 1.0),
            )

        # Tests correct behavior
        evaluators = [
            {"feature": "LAST_NAME", "func": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match"}
        ]
        # write an assertion that no exception is raised
        AlgorithmPass(
            blocking_keys=[],
            evaluators=evaluators,
            rule="func:recordlinker.linking.matchers.rule_probabilistic_sum",
            possible_match_window=(0.75, 1.0),
        )

        evaluators = [
            {"feature": "FIRST_NAME:DL", "func": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match"}
        ]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=evaluators,
                rule="func:recordlinker.linking.matchers.rule_probabilistic_sum",
                possible_match_window=(0.75, 1.0),
            )

    def test_validate_rule(self):
        rule = "invalid.func"
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=[],
                rule=rule,
                possible_match_window=(0.75, 1.0),
            )
        rule = "func:recordlinker.linking.matchers.rule_probabilistic_sum"
        AlgorithmPass(
            blocking_keys=[],
            evaluators=[],
            rule=rule,
            possible_match_window=(0.75, 1.0),
        )

    def test_kwargs(self):
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=[],
                rule="func:recordlinker.linking.matchers.rule_probabilistic_sum",
                possible_match_window=(0.75, 1.0),
                kwargs={"invalid": "key"},
            )
        AlgorithmPass(
            blocking_keys=[],
            evaluators=[],
            rule="func:recordlinker.linking.matchers.rule_probabilistic_sum",
            possible_match_window=(0.75, 1.0),
            kwargs={
                "similarity_measure": "JaroWinkler",
                "thresholds": {"CITY": 0.95, "ADDRESS": 0.98},
                "threshold": 0.9,
                "log_odds": {"CITY": 12.0, "ADDRESS": 15.0},
            },
        )

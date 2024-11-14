"""
unit.schemas.test_algorithm.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.schemas.algorithm module.
"""

import pydantic
import pytest

from recordlinker.schemas.algorithm import AlgorithmPass


class TestAlgorithmPass:
    def test_validate_blocking_keys(self):
        keys = ["name", "birthDate"]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=keys,
                evaluators=[],
                rule="func:recordlinker.linking.matchers.eval_perfect_match",
                cluster_ratio=0.5,
            )
        keys = ["LAST_NAME", "BIRTHDATE", "ZIP"]
        # write an assertion that no exception is raised
        AlgorithmPass(
            blocking_keys=keys,
            evaluators=[],
            rule="func:recordlinker.linking.matchers.eval_perfect_match",
            cluster_ratio=0.5,
        )

    def test_validate_evaluators(self):
        evaluators = [{"feature":"name", "func":"func:recordlinker.linking.matchers.feature_match_any"}]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=evaluators,
                rule="func:recordlinker.linking.matchers.eval_perfect_match",
                cluster_ratio=0.5,
            )
        evaluators = [{"feature":"LAST_NAME", "func": "func:recordlinker.linking.matchers.unknown"}]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=evaluators,
                rule="func:recordlinker.linking.matchers.eval_perfect_match",
                cluster_ratio=0.5,
            )
        evaluators = [{"feature":"LAST_NAME", "func":"func:recordlinker.linking.matchers.eval_perfect_match"}]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=evaluators,
                rule="func:recordlinker.linking.matchers.eval_perfect_match",
                cluster_ratio=0.5,
            )
        evaluators = [{"feature": "LAST_NAME", "func": "func:recordlinker.linking.matchers.feature_match_any"}]
        # write an assertion that no exception is raised
        AlgorithmPass(
            blocking_keys=[],
            evaluators=evaluators,
            rule="func:recordlinker.linking.matchers.eval_perfect_match",
            cluster_ratio=0.5,
        )

    def test_validate_rule(self):
        rule = "invalid.func"
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=[],
                rule=rule,
                cluster_ratio=0.5,
            )
        rule = "func:recordlinker.linking.matchers.feature_match_any"
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=[],
                rule=rule,
                cluster_ratio=0.5,
            )
        rule = "func:recordlinker.linking.matchers.eval_perfect_match"
        AlgorithmPass(
            blocking_keys=[],
            evaluators=[],
            rule=rule,
            cluster_ratio=0.5,
        )

    def test_cluster_ratio(self):
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=[],
                rule="func:recordlinker.linking.matchers.eval_perfect_match",
                cluster_ratio=-1,
            )
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=[],
                rule="func:recordlinker.linking.matchers.eval_perfect_match",
                cluster_ratio=1.1,
            )
        AlgorithmPass(
            blocking_keys=[],
            evaluators=[],
            rule="func:recordlinker.linking.matchers.eval_perfect_match",
            cluster_ratio=0.56,
        )

    def test_kwargs(self):
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=[],
                evaluators=[],
                rule="func:recordlinker.linking.matchers.eval_perfect_match",
                cluster_ratio=0.5,
                kwargs={"invalid": "key"}
            )
        AlgorithmPass(
            blocking_keys=[],
            evaluators=[],
            rule="func:recordlinker.linking.matchers.eval_perfect_match",
            cluster_ratio=0.5,
            kwargs={
                "similarity_measure": "JaroWinkler",
                "thresholds": {"CITY": 0.95, "ADDRESS": 0.98},
                "threshold": 0.9,
                "log_odds": {"CITY": 12.0, "ADDRESS": 15.0},
                "true_match_threshold": 0.8,
            }
        )

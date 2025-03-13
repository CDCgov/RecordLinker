"""
unit.schemas.test_algorithm.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.schemas.algorithm module.
"""

import pydantic
import pytest

from recordlinker.linking import matchers
from recordlinker.models.mpi import BlockingKey
from recordlinker.schemas.algorithm import AlgorithmPass
from recordlinker.schemas.algorithm import EvaluationContext
from recordlinker.schemas.algorithm import Evaluator
from recordlinker.schemas.algorithm import LogOdd
from recordlinker.schemas.pii import Feature


class TestLogOdd:
    def test_validate_feature(self):
        with pytest.raises(pydantic.ValidationError):
            LogOdd(feature="UNKNOWN", value=0)

        with pytest.raises(pydantic.ValidationError):
            LogOdd(feature="FIRST_NAME", value=-1.4)

        LogOdd(feature="IDENTIFIER", value=0)
        LogOdd(feature="ZIP", value=12.4)
        LogOdd(feature="IDENTIFIER:MR", value=19.5)


class TestEvaluationContext:
    def test_validate_belongingness_ratio(self):
        with pytest.raises(pydantic.ValidationError):
            EvaluationContext(belongingness_ratio=(0.9, 0.75))
        EvaluationContext(belongingness_ratio=(0.75, 0.9))
        EvaluationContext(belongingness_ratio=(0.9, 0.9))

    def test_serialize_belongingness_ratio(self):
        assert EvaluationContext().serialize_belongingness_ratio((0.8, 0.9)) == [0.8, 0.9]

    def test_belongingness_ratio_lower_bound(self):
        context = EvaluationContext(belongingness_ratio=(0.6, 0.9))
        assert context.belongingness_ratio_lower_bound == 0.6

    def test_belongingness_ratio_upper_bound(self):
        context = EvaluationContext(belongingness_ratio=(0.6, 0.9))
        assert context.belongingness_ratio_upper_bound == 0.9

    def test_get_log_odds(self):
        context = EvaluationContext(
            log_odds=[
                {"feature": "FIRST_NAME", "value": 6.5},
                {"feature": "IDENTIFIER", "value": 9},
                {"feature": "IDENTIFIER:SS", "value": 12},
            ]
        )
        assert context.get_log_odds(Feature.parse("LAST_NAME")) is None
        assert context.get_log_odds(Feature.parse("FIRST_NAME")) == 6.5
        assert context.get_log_odds(Feature.parse("IDENTIFIER")) == 9
        assert context.get_log_odds(Feature.parse("IDENTIFIER:SS")) == 12
        assert context.get_log_odds(Feature.parse("IDENTIFIER:MR")) == 9


class TestEvaluator:
    def test_validate_feature(self):
        with pytest.raises(pydantic.ValidationError):
            Evaluator(
                feature="UNKNOWN",
                func="func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match",
            )

        Evaluator(
            feature="IDENTIFIER",
            func="func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match",
        )
        Evaluator(
            feature="ZIP",
            func="func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match",
        )
        Evaluator(
            feature="IDENTIFIER:MR",
            func="func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match",
        )

    def test_serialize_func(self):
        evaluator = Evaluator(
            feature="IDENTIFIER",
            func="func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match",
        )
        assert (
            evaluator.serialize_func(matchers.FeatureFunc.COMPARE_PROBABILISTIC_FUZZY_MATCH)
            == "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match"
        )
        assert (
            evaluator.serialize_func(matchers.FeatureFunc.COMPARE_PROBABILISTIC_EXACT_MATCH)
            == "func:recordlinker.linking.matchers.compare_probabilistic_exact_match"
        )


class TestAlgorithmPass:
    def test_validate_blocking_keys(self):
        keys = ["name", "birthDate"]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=keys,
                evaluators=[],
                rule="func:recordlinker.linking.matchers.rule_probabilistic_match",
                true_match_threshold=0,
            )
        keys = ["LAST_NAME", "BIRTHDATE", "ZIP"]
        # write an assertion that no exception is raised
        AlgorithmPass(
            blocking_keys=keys,
            evaluators=[],
            rule="func:recordlinker.linking.matchers.rule_probabilistic_match",
            true_match_threshold=0,
        )

    def test_serialize_blocking_keys(self):
        _pass = AlgorithmPass(blocking_keys=[], evaluators=[], true_match_threshold=0)
        assert _pass.serialize_blocking_keys([BlockingKey.BIRTHDATE]) == ["BIRTHDATE"]
        assert _pass.serialize_blocking_keys([BlockingKey.FIRST_NAME, BlockingKey.LAST_NAME]) == [
            "FIRST_NAME",
            "LAST_NAME",
        ]

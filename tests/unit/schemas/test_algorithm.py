"""
unit.schemas.test_algorithm.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.schemas.algorithm module.
"""

import pydantic
import pytest

from recordlinker.linking import matchers
from recordlinker.models.mpi import BlockingKey
from recordlinker.schemas.algorithm import Algorithm
from recordlinker.schemas.algorithm import AlgorithmPass
from recordlinker.schemas.algorithm import Defaults
from recordlinker.schemas.algorithm import EvaluationContext
from recordlinker.schemas.algorithm import Evaluator
from recordlinker.schemas.algorithm import LogOdd
from recordlinker.schemas.pii import Feature


class TestDefaults:
    def test_validate_fuzzy_match_threshold(self):
        with pytest.raises(pydantic.ValidationError):
            Defaults(fuzzy_match_threshold=-0.5)
        with pytest.raises(pydantic.ValidationError):
            Defaults(fuzzy_match_threshold=1.1)
        Defaults(fuzzy_match_threshold=0.5)

    def test_validate_fuzzy_match_measure(self):
        with pytest.raises(pydantic.ValidationError):
            Defaults(fuzzy_match_measure="UNKNOWN")
        Defaults(fuzzy_match_measure="JaroWinkler")
        Defaults(fuzzy_match_measure="Levenshtein")


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
                func="COMPARE_PROBABILISTIC_FUZZY_MATCH",
            )

        Evaluator(
            feature="IDENTIFIER",
            func="COMPARE_PROBABILISTIC_FUZZY_MATCH",
        )
        Evaluator(
            feature="ZIP",
            func="COMPARE_PROBABILISTIC_FUZZY_MATCH",
        )
        Evaluator(
            feature="IDENTIFIER:MR",
            func="COMPARE_PROBABILISTIC_FUZZY_MATCH",
        )

    def test_serialize_func(self):
        evaluator = Evaluator(
            feature="IDENTIFIER",
            func="COMPARE_PROBABILISTIC_FUZZY_MATCH",
        )
        assert (
            evaluator.serialize_func(matchers.FeatureFunc.COMPARE_PROBABILISTIC_FUZZY_MATCH)
            == "COMPARE_PROBABILISTIC_FUZZY_MATCH"
        )
        assert (
            evaluator.serialize_func(matchers.FeatureFunc.COMPARE_PROBABILISTIC_EXACT_MATCH)
            == "COMPARE_PROBABILISTIC_EXACT_MATCH"
        )


class TestAlgorithmPass:
    def test_validate_blocking_keys(self):
        keys = ["name", "birthDate"]
        with pytest.raises(pydantic.ValidationError):
            AlgorithmPass(
                blocking_keys=keys,
                evaluators=[],
                true_match_threshold=0,
            )
        keys = ["LAST_NAME", "BIRTHDATE", "ZIP"]
        # write an assertion that no exception is raised
        AlgorithmPass(
            blocking_keys=keys,
            evaluators=[],
            true_match_threshold=0,
        )

    def test_serialize_blocking_keys(self):
        _pass = AlgorithmPass(blocking_keys=[], evaluators=[], true_match_threshold=0)
        assert _pass.serialize_blocking_keys([BlockingKey.BIRTHDATE]) == ["BIRTHDATE"]
        assert _pass.serialize_blocking_keys([BlockingKey.FIRST_NAME, BlockingKey.LAST_NAME]) == [
            "FIRST_NAME",
            "LAST_NAME",
        ]


class TestAlgorithm:
    def test_validate_log_odds_defined(self):
        with pytest.raises(pydantic.ValidationError):
            Algorithm(
                label="test",
                passes=[
                    AlgorithmPass(
                        blocking_keys=["BIRTHDATE"],
                        evaluators=[],
                        true_match_threshold=0,
                    )
                ]
            )
        with pytest.raises(pydantic.ValidationError):
            Algorithm(
                label="test",
                passes=[
                    AlgorithmPass(
                        blocking_keys=[],
                        evaluators=[{"feature": "FIRST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"}],
                        true_match_threshold=0,
                    )
                ]
            )
        Algorithm(
            label="test",
            evaluation_context={
                "log_odds": [
                    {"feature": "FIRST_NAME", "value": 7},
                    {"feature": "BIRTHDATE", "value": 10},
                ]
            },
            passes=[
                AlgorithmPass(
                    blocking_keys=["BIRTHDATE"],
                    evaluators=[{"feature": "FIRST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"}],
                    true_match_threshold=0,
                )
            ]
        )

    def test_validate_true_match_threshold(self):
        with pytest.raises(pydantic.ValidationError):
            Algorithm(
                label="test",
                evaluation_context={
                    "log_odds": [
                        {"feature": "FIRST_NAME", "value": 7},
                        {"feature": "BIRTHDATE", "value": 10},
                    ]
                },
                passes=[
                    AlgorithmPass(
                        blocking_keys=["BIRTHDATE"],
                        evaluators=[{"feature": "FIRST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"}],
                        true_match_threshold=7.3,
                    )
                ]
            )
        with pytest.raises(pydantic.ValidationError):
            Algorithm(
                label="test",
                evaluation_context={
                    "log_odds": [
                        {"feature": "FIRST_NAME", "value": 7},
                        {"feature": "LAST_NAME", "value": 6},
                        {"feature": "BIRTHDATE", "value": 10},
                    ]
                },
                passes=[
                    AlgorithmPass(
                        blocking_keys=["BIRTHDATE"],
                        evaluators=[
                            {"feature": "FIRST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"},
                            {"feature": "LAST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"},
                        ],
                        true_match_threshold=14,
                    )
                ]
            )
        Algorithm(
            label="test",
            evaluation_context={
                "log_odds": [
                    {"feature": "FIRST_NAME", "value": 7},
                    {"feature": "LAST_NAME", "value": 6},
                    {"feature": "BIRTHDATE", "value": 10},
                ]
            },
            passes=[
                AlgorithmPass(
                    blocking_keys=["BIRTHDATE"],
                    evaluators=[
                        {"feature": "FIRST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"},
                        {"feature": "LAST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"},
                    ],
                    true_match_threshold=12.9,
                )
            ]
        )

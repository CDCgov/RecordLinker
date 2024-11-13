"""
unit.linking.test_algorithm_service.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.linking.algorithm_service module.
"""

import pytest
import sqlalchemy.exc
from sqlalchemy.sql import select

from recordlinker import models
from recordlinker import schemas
from recordlinker.linking import algorithm_service


def test_list_algorithms(session):
    algo1 = models.Algorithm(label="basic", is_default=True, description="First algorithm")
    algo2 = models.Algorithm(label="enhanced", description="Second algorithm")
    session.add(algo1)
    session.add(algo2)
    session.commit()

    algorithms = algorithm_service.list_algorithms(session)
    assert len(algorithms) == 2
    assert [a.label for a in algorithms] == ["basic", "enhanced"]


def test_default_algorithm(session):
    assert algorithm_service.default_algorithm(session) is None

    algo1 = models.Algorithm(label="basic", is_default=False, description="First algorithm")
    algo2 = models.Algorithm(label="enhanced", is_default=True, description="Second algorithm")
    session.add(algo1)
    session.add(algo2)
    session.commit()

    default = algorithm_service.default_algorithm(session)
    assert default == algo2


class TestGetAlgorithm:
    def test_get_algorithm_match(self, session):
        testLabel = "dibss_basic"
        algo1 = models.Algorithm(label=testLabel, is_default=True, description="First algorithm")
        session.add(algo1)
        session.commit()

        algorithm = algorithm_service.get_algorithm(session, testLabel)
        assert algorithm == algo1

    def test_get_algorithm_no_match(self, session):
        # inserting the default algorithm
        algo1 = models.Algorithm(
            label="dibss_basic", is_default=True, description="First algorithm"
        )
        session.add(algo1)
        session.commit()

        algorithm = algorithm_service.get_algorithm(session, "WRONG_LABEL")
        assert algorithm is None


class TestLoadAlgorithm:
    def test_load_algorithm_created(self, session):
        data = schemas.Algorithm(
            label="dibss-basic",
            description="First algorithm",
            passes=[
                schemas.AlgorithmPass(
                    blocking_keys=["FIRST_NAME"],
                    evaluators=[
                        {
                            "feature": "ZIP",
                            "func": "func:recordlinker.linking.matchers.feature_match_any",
                        }
                    ],
                    rule="func:recordlinker.linking.matchers.eval_perfect_match",
                    cluster_ratio=0.8,
                )
            ],
        )
        obj, created = algorithm_service.load_algorithm(session, data)
        session.flush()
        assert created is True
        assert obj.id == 1
        assert obj.label == "dibss-basic"
        assert obj.description == "First algorithm"
        assert len(obj.passes) == 1
        assert obj.passes[0].algorithm_id == 1
        assert obj.passes[0].blocking_keys == ["FIRST_NAME"]
        assert obj.passes[0].evaluators == [
            {"feature": "ZIP", "func": "func:recordlinker.linking.matchers.feature_match_any"}
        ]
        assert obj.passes[0].rule == "func:recordlinker.linking.matchers.eval_perfect_match"
        assert obj.passes[0].cluster_ratio == 0.8

    def test_load_algorithm_updated(self, session):
        data = schemas.Algorithm(
            label="dibss-basic",
            description="First algorithm",
            passes=[
                schemas.AlgorithmPass(
                    blocking_keys=["FIRST_NAME"],
                    evaluators=[
                        {
                            "feature": "ZIP",
                            "func": "func:recordlinker.linking.matchers.feature_match_any",
                        }
                    ],
                    rule="func:recordlinker.linking.matchers.eval_perfect_match",
                    cluster_ratio=0.8,
                )
            ],
        )
        obj, created = algorithm_service.load_algorithm(session, data)
        session.flush()
        data.description = "Updated description"
        data.passes[0].blocking_keys = ["LAST_NAME"]
        obj, created = algorithm_service.load_algorithm(session, data, obj)
        session.flush()
        assert created is False
        assert obj.id == 1
        assert obj.label == "dibss-basic"
        assert obj.description == "Updated description"
        assert len(obj.passes) == 1
        assert obj.passes[0].algorithm_id == 1
        assert obj.passes[0].blocking_keys == ["LAST_NAME"]
        assert obj.passes[0].evaluators == [
            {"feature": "ZIP", "func": "func:recordlinker.linking.matchers.feature_match_any"}
        ]
        assert obj.passes[0].rule == "func:recordlinker.linking.matchers.eval_perfect_match"
        assert obj.passes[0].cluster_ratio == 0.8


def test_delete_algorithm(session):
    with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
        algorithm_service.delete_algorithm(session, models.Algorithm())
    algo1 = models.Algorithm(label="basic", is_default=True, description="First algorithm")
    session.add(algo1)
    pass1 = models.AlgorithmPass(
        algorithm=algo1,
        blocking_keys=["FIRST_NAME"],
        evaluators=[
            {"feature": "ZIP", "func": "func:recordlinker.linking.matchers.feature_match_any"}
        ],
        rule="func:recordlinker.linking.matchers.eval_perfect_match",
        cluster_ratio=0.8,
    )
    session.add(pass1)
    session.commit()

    algorithm_service.delete_algorithm(session, algo1)
    assert session.execute(select(models.Algorithm)).scalar() is None
    assert session.execute(select(models.AlgorithmPass)).scalar() is None


def test_clear_algorithms(session):
    algo1 = models.Algorithm(label="basic", is_default=True, description="First algorithm")
    algo2 = models.Algorithm(label="enhanced", description="Second algorithm")
    session.add(algo1)
    session.add(algo2)
    pass1 = models.AlgorithmPass(
        algorithm=algo1,
        blocking_keys=["FIRST_NAME"],
        evaluators=[
            {"feature": "ZIP", "func": "func:recordlinker.linking.matchers.feature_match_any"}
        ],
        rule="func:recordlinker.linking.matchers.eval_perfect_match",
        cluster_ratio=0.8,
    )
    session.add(pass1)
    session.commit()

    algorithm_service.clear_algorithms(session)
    assert session.execute(select(models.Algorithm)).scalar() is None
    assert session.execute(select(models.AlgorithmPass)).scalar() is None

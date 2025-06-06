"""
unit.database.test_algorithm_service.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.database.algorithm_service module.
"""

import pytest
import sqlalchemy.exc
from sqlalchemy.sql import select

from recordlinker import models
from recordlinker import schemas
from recordlinker.database import algorithm_service


def test_list_algorithms(session):
    algo1 = models.Algorithm(label="default", description="First algorithm")
    algo2 = models.Algorithm(label="user", description="User uploaded algorithm")
    session.add(algo1)
    session.add(algo2)
    session.commit()

    algorithms = algorithm_service.list_algorithms(session)
    assert len(algorithms) == 2
    assert [a.label for a in algorithms] == ["default", "user"]


def test_default_algorithm(session):
    assert algorithm_service.default_algorithm(session) is None

    algo1 = models.Algorithm(label="default", is_default=True, description="First algorithm")
    session.add(algo1)
    session.commit()

    default = algorithm_service.default_algorithm(session)
    assert default == algo1


class TestGetAlgorithm:
    def test_get_algorithm_match(self, session):
        testLabel = "dibbs-default"
        algo1 = models.Algorithm(label="dibbs-default", description="First algorithm")
        session.add(algo1)
        session.commit()

        algorithm = algorithm_service.get_algorithm(session, testLabel)
        assert algorithm == algo1

    def test_get_algorithm_no_match(self, session):
        # inserting the default algorithm
        algo1 = models.Algorithm(label="default", description="First algorithm")
        session.add(algo1)
        session.commit()

        algorithm = algorithm_service.get_algorithm(session, "WRONG_LABEL")
        assert algorithm is None


class TestLoadAlgorithm:
    def test_load_algorithm_created(self, session):
        data = schemas.Algorithm(
            label="dibbs-test",
            description="First algorithm",
            max_missing_allowed_proportion=0.5,
            missing_field_points_proportion=0.5,
            algorithm_context={
                "log_odds": [
                    {"feature": "FIRST_NAME", "value": 6.8},
                    {"feature": "ZIP", "value": 5.0},
                ]
            },
            passes=[
                schemas.AlgorithmPass(
                    blocking_keys=["FIRST_NAME"],
                    evaluators=[
                        {
                            "feature": "ZIP",
                            "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH",
                        }
                    ],
                    possible_match_window=(0.75, 1.0),
                )
            ],
            
        )
        obj, created = algorithm_service.load_algorithm(session, data)
        session.flush()
        assert created is True
        assert obj.id == 1
        assert obj.label == "dibbs-test"
        assert obj.description == "First algorithm"
        assert obj.algorithm_context == {
            "include_multiple_matches": True,
            "log_odds": [
                {"feature": "FIRST_NAME", "value": 6.8},
                {"feature": "ZIP", "value": 5.0},
            ],
            "skip_values": [],
            "advanced": {
                "fuzzy_match_threshold": 0.9,
                "fuzzy_match_measure": "JaroWinkler",
                "max_missing_allowed_proportion": 0.5,
                "missing_field_points_proportion": 0.5,
            },
        }
        assert len(obj.passes) == 1
        assert obj.passes[0] == {
            "label": "BLOCK_first_name_MATCH_zip",
            "description": None,
            "blocking_keys": ["FIRST_NAME"],
            "evaluators": [
                {
                    "feature": "ZIP",
                    "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH",
                    "fuzzy_match_threshold": None,
                    "fuzzy_match_measure": None,
                }
            ],
            "possible_match_window": (0.75, 1.0)
        }

    def test_load_algorithm_updated(self, session):
        data = schemas.Algorithm(
            label="dibbs-test",
            description="First algorithm",
            max_missing_allowed_proportion=0.5,
            missing_field_points_proportion=0.5,
            algorithm_context={
                "log_odds": [
                    {"feature": "FIRST_NAME", "value": 6.8},
                    {"feature": "ZIP", "value": 5.0},
                ]
            },
            passes=[
                schemas.AlgorithmPass(
                    blocking_keys=["FIRST_NAME"],
                    evaluators=[
                        {
                            "feature": "ZIP",
                            "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH",
                        }
                    ],
                    possible_match_window=(0.75, 1.0),
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
        assert obj.label == "dibbs-test"
        assert obj.description == "Updated description"
        assert obj.algorithm_context == {
            "include_multiple_matches": True,
            "log_odds": [
                {"feature": "FIRST_NAME", "value": 6.8},
                {"feature": "ZIP", "value": 5.0},
            ],
            "skip_values": [],
            "advanced": {
                "fuzzy_match_threshold": 0.9,
                "fuzzy_match_measure": "JaroWinkler",
                "max_missing_allowed_proportion": 0.5,
                "missing_field_points_proportion": 0.5,
            },
        }
        assert len(obj.passes) == 1
        assert obj.passes[0] == {
            "label": "BLOCK_first_name_MATCH_zip",
            "description": None,
            "blocking_keys": ["LAST_NAME"],
            "evaluators": [
                {
                    "feature": "ZIP",
                    "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH",
                    "fuzzy_match_threshold": None,
                    "fuzzy_match_measure": None,
                }
            ],
            "possible_match_window": (0.75, 1.0)
        }


def test_delete_algorithm(session):
    with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
        algorithm_service.delete_algorithm(session, models.Algorithm())
    algo1 = models.Algorithm(label="default", is_default=True, description="First algorithm")
    session.add(algo1)
    session.commit()

    algorithm_service.delete_algorithm(session, algo1)
    assert session.execute(select(models.Algorithm)).scalar() is None


def test_clear_algorithms(session):
    algo1 = models.Algorithm(label="default", is_default=True, description="First algorithm")
    session.add(algo1)
    session.commit()

    algorithm_service.clear_algorithms(session)
    assert session.execute(select(models.Algorithm)).scalar() is None

"""
unit.models.test_algorithm.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.models.algorithm module.
"""
import unittest.mock

import pytest

from recordlinker import config
from recordlinker.linking import matchers
from recordlinker.models import algorithm as models


class TestAlgorithm:
    def test_single_default_algorithm(self, session):
        """
        Tests that only one algorithm can be default in the Algorithm table
        """
        # first algorithm is_default set to True
        algo1 = models.Algorithm(
            label="Algorithm 1", is_default=True, description="First algorithm"
        )
        session.add(algo1)
        session.commit()

        # create another algorithm and try to set is_default as True
        algo2 = models.Algorithm(
            label="Algorithm 2", is_default=True, description="Second algorithm"
        )
        session.add(algo2)

        with pytest.raises(ValueError, match="There can only be one default algorithm"):
            session.commit()

    def test_set_default_when_none_exists(self, session):
        """
        Tests that you can update an algorithm to be the default if no other default exists
        """
        # is_default set to false
        algo1 = models.Algorithm(
            label="Algorithm 1", is_default=False, description="First algorithm"
        )
        session.add(algo1)
        session.commit()

        # try setting it as the default
        algo1.is_default = True
        session.add(algo1)

        session.commit()

    def test_update_existing_default(self, session):
        """
        Tests that updating the default algorithm do not raise ValueErrors
        """
        algo1 = models.Algorithm(
            label="Algorithm 1", is_default=True, description="First algorithm"
        )
        session.add(algo1)
        session.commit()

        # update the same algorithm
        algo1.description = "Updated algorithm"
        session.add(algo1)

        # should not raise any value errors
        session.commit()

    def test_from_dict_no_passes(self):
        data = {
            "label": "Algorithm 1",
            "description": "First algorithm",
        }
        algo = models.Algorithm.from_dict(**data)
        assert algo.label == "Algorithm 1"
        assert algo.description == "First algorithm"
        assert algo.passes == []

    def test_from_dict_with_passes(self):
        data = {
            "label": "Algorithm 1",
            "description": "First algorithm",
            "belongingness_ratio": (0.75, 1.0),
            "passes": [
                {
                    "blocking_keys": ["ZIP"],
                    "evaluators": {
                        "FIRST_NAME": "func:recordlinker.linking.matchers.feature_match_exact",
                        "LAST_NAME": "func:recordlinker.linking.matchers.feature_match_exact",
                    },
                    "rule": "func:recordlinker.linking.matchers.eval_perfect_match",
                }
            ],
        }
        algo = models.Algorithm.from_dict(**data)
        assert algo.label == "Algorithm 1"
        assert algo.description == "First algorithm"
        assert algo.belongingness_ratio == (0.75, 1.0)
        assert len(algo.passes) == 1
        assert algo.passes[0].blocking_keys == ["ZIP"]
        assert algo.passes[0].evaluators == {
            "FIRST_NAME": "func:recordlinker.linking.matchers.feature_match_exact",
            "LAST_NAME": "func:recordlinker.linking.matchers.feature_match_exact",
        }
        assert algo.passes[0].rule == "func:recordlinker.linking.matchers.eval_perfect_match"


class TestAlgorithmPass:
    def test_bound_evaluators(self):
        """
        Tests that the bound_evaluators method returns the correct functions
        """
        ap = models.AlgorithmPass(
            evaluators={"BIRTHDATE": "func:recordlinker.linking.matchers.feature_match_any"}
        )
        assert ap.bound_evaluators() == {"BIRTHDATE": matchers.feature_match_any}
        ap.evaluators = {"BIRTHDATE": "func:recordlinker.linking.matchers.feature_match_exact"}
        assert ap.bound_evaluators() == {"BIRTHDATE": matchers.feature_match_exact}
        ap.evaluators = {"BIRTHDATE": "func:invalid"}
        with pytest.raises(ValueError, match="Failed to convert string to callable"):
            ap.bound_evaluators()

    def test_bound_rule(self):
        """
        Tests that the bound_rule method returns the correct function
        """
        ap = models.AlgorithmPass(rule="func:recordlinker.linking.matchers.eval_perfect_match")
        assert ap.bound_rule() == matchers.eval_perfect_match
        ap.rule = "func:recordlinker.linking.matchers.eval_log_odds_cutoff"
        assert ap.bound_rule() == matchers.eval_log_odds_cutoff
        ap.rule = "func:recordlinker.linking.matchers.invalid"
        with pytest.raises(ValueError, match="Failed to convert string to callable"):
            ap.bound_rule()


class TestCreateInitialAlgorithms:
    def test_invalid_file(self, monkeypatch, session):
        """
        Tests that an invalid file raises a FileNotFoundError
        """
        monkeypatch.setattr(config.settings, "initial_algorithms", "invalid_file.json")
        with pytest.raises(config.ConfigurationError, match="Error loading initial algorithms"):
            models.create_initial_algorithms(None, session.connection())

    def test_no_default(self, monkeypatch, session):
        """
        Tests that the initial algorithms are created without a default algorithm
        """
        monkeypatch.setattr(config.settings, "initial_algorithms", "file.json")
        with unittest.mock.patch("recordlinker.utils.path.read_json") as read_json:
            read_json.return_value = [{"is_default": False}]
            with pytest.raises(config.ConfigurationError, match="No default algorithm found"):
                models.create_initial_algorithms(None, session.connection())

    def test_invalid_algorithm(self, monkeypatch, session):
        """
        Tests that an invalid algorithm raises a ValueError
        """
        monkeypatch.setattr(config.settings, "initial_algorithms", "file.json")
        with unittest.mock.patch("recordlinker.utils.path.read_json") as read_json:
            read_json.return_value = [{"labell": "Algorithm 1", "is_default": True}]
            with pytest.raises(config.ConfigurationError, match="Error creating initial algorithms"):
                models.create_initial_algorithms(None, session.connection())

    def test_create_initial_algorithms(self, monkeypatch, session):
        """
        Tests that the initial algorithms are created
        """
        monkeypatch.setattr(config.settings, "initial_algorithms", "file.json")
        with unittest.mock.patch("recordlinker.utils.path.read_json") as read_json:
            read_json.return_value = [{"label": "Algorithm 1", "is_default": True}]
            models.create_initial_algorithms(None, session.connection())
            assert session.query(models.Algorithm).count() == 1
            assert session.query(models.Algorithm).first().is_default is True
            assert session.query(models.Algorithm).first().label == "Algorithm 1"

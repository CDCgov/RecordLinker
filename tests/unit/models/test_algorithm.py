"""
unit.models.test_algorithm.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.models.algorithm module.
"""

import pytest

from recordlinker import models
from recordlinker.linking import matchers


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


class TestAlgorithmPass:
    def test_bound_evaluators(self):
        """
        Tests that the bound_evaluators method returns the correct functions
        """
        ap = models.AlgorithmPass(evaluators={"BIRTHDATE": "func:recordlinker.linking.matchers.feature_match_any"})
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

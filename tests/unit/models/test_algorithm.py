"""
unit.models.test_algorithm.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.models.algorithm module.
"""

import pytest

from recordlinker import models


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

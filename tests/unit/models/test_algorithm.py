"""
unit.models.test_algorithm.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.models.algorithm module.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from recordlinker import models
from recordlinker.config import settings


@pytest.fixture(scope="function")
def setup_database():
    engine = create_engine(settings.test_db_uri)
    Session = scoped_session(sessionmaker(bind=engine))
    models.Base.metadata.create_all(engine)  # Create tables

    yield Session  # Provide the session object to tests

    # Cleanup after tests
    models.Base.metadata.drop_all(engine)
    Session.remove()


class TestAlgorithm:
    def test_single_default_algorithm(self, setup_database):
        """
        Tests that only one algorithm can be default in the Algorithm table
        """

        session = setup_database()

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

    def test_set_default_when_none_exists(self, setup_database):
        """
        Tests that you can update an algorithm to be the default if no other default exists
        """

        session = setup_database()

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

    def test_update_existing_default(self, setup_database):
        """
        Tests that updating the default algorithm do not raise ValueErrors
        """

        session = setup_database()

        # algorithm is_default set to True
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

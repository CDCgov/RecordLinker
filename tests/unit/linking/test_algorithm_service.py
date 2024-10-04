"""
unit.linking.test_algorithm_service.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.linking.algorithm_service module.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy import orm

from recordlinker import models
from recordlinker.config import settings
from recordlinker.linking import algorithm_service


@pytest.fixture(scope="function")
def session():
    engine = create_engine(settings.test_db_uri)
    models.Base.metadata.create_all(engine)

    # Create a new session factory and scoped session
    Session = orm.scoped_session(orm.sessionmaker(bind=engine))
    session = Session()

    yield session  # This is where the testing happens

    session.close()  # Cleanup after test
    models.Base.metadata.drop_all(engine)  # Drop all tables after the test

def test_get_all_algorithm_labels(session):
    testLabel = "DIBBS_BASIC"
    algo1 = models.Algorithm(label=testLabel, is_default=True, description="First algorithm")
    session.add(algo1)
    session.commit()
    
    algorithmsList = algorithm_service.get_all_algorithm_labels(session)
    assert algorithmsList == [testLabel]

class TestGetAlgorithmByLabel:
    def test_get_algorithm_by_label_match(self, session):
        testLabel = "DIBBS_BASIC"
        algo1 = models.Algorithm(label=testLabel, is_default=True, description="First algorithm")
        session.add(algo1)
        session.commit()
        
        algorithm = algorithm_service.get_algorithm_by_label(session, testLabel)
        assert algorithm == algo1

    def test_get_algorithm_by_label_no_match(self, session):
        #inserting the default algorithm
        algo1 = models.Algorithm(label="DIBBS_BASIC", is_default=True, description="First algorithm")
        session.add(algo1)
        session.commit()
        
        algorithm = algorithm_service.get_algorithm_by_label(session, "WRONG_LABEL")
        assert algorithm is None

    def test_get_algorithm_by_label_empty(self, session):
        #inserting the default algorithm
        algo1 = models.Algorithm(label="DIBBS_BASIC", is_default=True, description="First algorithm")
        session.add(algo1)
        session.commit()
        
        algorithm = algorithm_service.get_algorithm_by_label(session, None)
        
        #returned algorithm should just be the default
        assert algorithm == algo1

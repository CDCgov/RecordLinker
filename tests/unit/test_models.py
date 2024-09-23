"""
unit.test_models.py
~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.linkage.models module.
"""

import datetime

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


class TestBlockingKey:
    def test_extract_birthdate(self):
        data = {"dob": "01/01/1980"}
        assert models.BlockingKey.BIRTHDATE.to_value(data) == set()
        data = {"birthdate": "1980-01-01"}
        assert models.BlockingKey.BIRTHDATE.to_value(data) == {"1980-01-01"}
        data = {"birthdate": datetime.date(1980, 1, 1)}
        assert models.BlockingKey.BIRTHDATE.to_value(data) == {"1980-01-01"}
        data = {"birthdate": "01/01/1980"}
        assert models.BlockingKey.BIRTHDATE.to_value(data) == {"1980-01-01"}
        data = {"birthdate": ""}
        assert models.BlockingKey.BIRTHDATE.to_value(data) == set()

    def test_extract_mrn_last_four(self):
        data = {"ssn": "123456789"}
        assert models.BlockingKey.MRN.to_value(data) == set()
        data = {"mrn": None}
        assert models.BlockingKey.MRN.to_value(data) == set()
        data = {"mrn": "123456789"}
        assert models.BlockingKey.MRN.to_value(data) == {"6789"}
        data = {"mrn": "89"}
        assert models.BlockingKey.MRN.to_value(data) == {"89"}

    def test_extract_sex(self):
        data = {"gender": "M"}
        assert models.BlockingKey.SEX.to_value(data) == set()
        data = {"sex": ""}
        assert models.BlockingKey.SEX.to_value(data) == set()
        data = {"sex": "M"}
        assert models.BlockingKey.SEX.to_value(data) == {"m"}
        data = {"sex": "Male"}
        assert models.BlockingKey.SEX.to_value(data) == {"m"}
        data = {"sex": "f"}
        assert models.BlockingKey.SEX.to_value(data) == {"f"}
        data = {"sex": "FEMALE"}
        assert models.BlockingKey.SEX.to_value(data) == {"f"}
        data = {"sex": "other"}
        assert models.BlockingKey.SEX.to_value(data) == {"u"}
        data = {"sex": "unknown"}
        assert models.BlockingKey.SEX.to_value(data) == {"u"}
        data = {"sex": "?"}
        assert models.BlockingKey.SEX.to_value(data) == {"u"}

    def test_extract_zipcode(self):
        data = {"zipcode": "12345"}
        assert models.BlockingKey.ZIP.to_value(data) == set()
        data = {"address": [{"postal_code": None}]}
        assert models.BlockingKey.ZIP.to_value(data) == set()
        data = {"address": [{"postal_code": "12345"}]}
        assert models.BlockingKey.ZIP.to_value(data) == {"12345"}
        data = {"address": [{"postal_code": "12345-6789"}]}
        assert models.BlockingKey.ZIP.to_value(data) == {"12345"}
        data = {"address": [{"postal_code": "12345-6789"}, {"postal_code": "54321"}]}
        assert models.BlockingKey.ZIP.to_value(data) == {"12345", "54321"}

    def test_extract_first_name_first_four(self):
        data = {"first_name": "John"}
        assert models.BlockingKey.FIRST_NAME.to_value(data) == set()
        data = {"name": [{"given": [""], "family": "Doe"}]}
        assert models.BlockingKey.FIRST_NAME.to_value(data) == set()
        data = {"name": [{"given": ["John", "Jane"], "family": "Doe"}]}
        assert models.BlockingKey.FIRST_NAME.to_value(data) == {"John", "Jane"}
        data = {"name": [{"given": ["Janet", "Johnathon"], "family": "Doe"}, {"given": ["Jane"], "family": "Smith"}]}
        assert models.BlockingKey.FIRST_NAME.to_value(data) == {"Jane", "John"}

    def test_extract_last_name_first_four(self):
        data = {"last_name": "Doe"}
        assert models.BlockingKey.LAST_NAME.to_value(data) == set()
        data = {"name": [{"family": ""}]}
        assert models.BlockingKey.LAST_NAME.to_value(data) == set()
        data = {"name": [{"family": "Doe"}]}
        assert models.BlockingKey.LAST_NAME.to_value(data) == {"Doe"}
        data = {"name": [{"family": "Smith"}, {"family": "Doe"}]}
        assert models.BlockingKey.LAST_NAME.to_value(data) == {"Smit", "Doe"}


class TestAlgorithm:
    def test_single_default_algorithm(self, setup_database):
        """
        Tests that only one algorithm can be default in the Algorithm table
        """

        session = setup_database()

        # first algorithm is_default set to True
        algo1 = models.Algorithm(label="Algorithm 1", is_default=True, description="First algorithm")
        session.add(algo1)
        session.commit()

        # create another algorithm and try to set is_default as True
        algo2 = models.Algorithm(label="Algorithm 2", is_default=True, description="Second algorithm")
        session.add(algo2)
        
        with pytest.raises(ValueError, match="There can only be one default algorithm"):
            session.commit()

    def test_set_default_when_none_exists(self, setup_database):
        """
        Tests that you can update an algorithm to be the default if no other default exists
        """

        session = setup_database()

        # is_default set to false   
        algo1 = models.Algorithm(label="Algorithm 1", is_default=False, description="First algorithm")
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
        algo1 = models.Algorithm(label="Algorithm 1", is_default=True, description="First algorithm")
        session.add(algo1)
        session.commit()

        # update the same algorithm 
        algo1.description = "Updated algorithm"
        session.add(algo1)
        
        # should not raise any value errors
        session.commit()

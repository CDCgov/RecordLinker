"""
unit.test_simple_mpi.py
~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.linkage.simple_mpi module.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from recordlinker.config import settings
from recordlinker.linkage import models
from recordlinker.linkage import simple_mpi


# Fixture to create a new in-memory SQLite database and session for each test
@pytest.fixture(scope="function")
def session():
    # Create an in-memory SQLite engine
    engine = create_engine(settings.test_db_uri)
    models.Base.metadata.create_all(engine)  # Create all tables in the in-memory database

    # Create a new session factory and scoped session
    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()

    yield session  # This is where the testing happens

    session.close()  # Cleanup after test
    models.Base.metadata.drop_all(engine)  # Drop all tables after the test


@pytest.fixture(scope="function")
def new_patient(session):
    patient = models.Patient(person=models.Person(), data={})
    session.add(patient)
    session.flush()
    return patient


class TestInsertBlockingKeys:
    def test_patient_no_blocking_keys(self, session, new_patient):
        new_patient.data = {"name": "John Doe"}
        assert simple_mpi.insert_blocking_keys(session, new_patient) == []

    def test_patient_with_blocking_keys(self, session, new_patient):
        new_patient.data = {"name": [{"given": ["Johnathon", "Bill",], "family": "Smith"}], "birthdate": "01/01/1980"}
        keys = simple_mpi.insert_blocking_keys(session, new_patient)
        assert len(keys) == 4
        assert keys[0].patient_id == new_patient.id
        assert keys[0].blockingkey == models.BlockingKey.BIRTHDATE.id
        assert keys[0].value == "1980-01-01"
        assert keys[1].patient_id == new_patient.id
        assert keys[1].blockingkey == models.BlockingKey.FIRST_NAME.id
        assert keys[1].value == "John"
        assert keys[2].patient_id == new_patient.id
        assert keys[2].blockingkey == models.BlockingKey.FIRST_NAME.id
        assert keys[2].value == "Bill"
        assert keys[3].patient_id == new_patient.id
        assert keys[3].blockingkey == models.BlockingKey.LAST_NAME.id
        assert keys[3].value == "Smit"


class TestInsertMatchedPatient:
    def test_no_person(self, session):
        data = {"name": [{"given": ["Johnathon", "Bill",], "family": "Smith"}], "birthdate": "01/01/1980"}
        patient = simple_mpi.insert_matched_patient(session, data)
        assert patient.person_id is not None
        assert patient.data == data
        assert patient.external_person_id is None
        assert patient.external_person_source is None
        assert patient.person.internal_id is not None
        assert patient.person.id == patient.person_id
        assert len(patient.blocking_values) == 4

    def test_no_person_with_external_id(self, session):
        data = {"name": [{"given": ["Johnathon",], "family": "Smith"}], "birthdate": "01/01/1980"}
        patient = simple_mpi.insert_matched_patient(session, data, external_person_id="123456")
        assert patient.person_id is not None
        assert patient.data == data
        assert patient.external_person_id == "123456"
        assert patient.external_person_source == "IRIS"
        assert patient.person.internal_id is not None
        assert patient.person.id is not None
        assert patient.person.id == patient.person_id
        assert len(patient.blocking_values) == 3

    def test_with_person(self, session):
        person = models.Person()
        session.add(person)
        session.flush()
        data = {"name": [{"given": ["George",], "family": "Harrison"}], "birthdate": "1943-2-25"}
        patient = simple_mpi.insert_matched_patient(session, data, person_id=person.id)
        assert patient.person_id == person.id
        assert patient.data == data
        assert patient.external_person_id is None
        assert patient.external_person_source is None
        assert len(patient.blocking_values) == 3

    def test_with_person_and_external_patient_id(self, session):
        person = models.Person()
        session.add(person)
        session.flush()
        data = {"name": [{"given": ["George",], "family": "Harrison"}]}
        patient = simple_mpi.insert_matched_patient(session, data, person_id=person.id, external_patient_id="abc")
        assert patient.person_id == person.id
        assert patient.data == data
        assert patient.external_patient_id == "abc"
        assert patient.external_person_id is None
        assert patient.external_person_source is None
        assert len(patient.blocking_values) == 2


class TestGetBlockData:
    @pytest.fixture
    def prime_index(self, session):
        data = [
            {"name": [{"given": ["Johnathon", "Bill",], "family": "Smith"}], "birthdate": "01/01/1980"},
            {"name": [{"given": ["George",], "family": "Harrison"}], "birthdate": "1943-2-25"},
            {"name": [{"given": ["John",], "family": "Doe"}], "birthdate": "1980-01-01"},
            {"name": [{"given": ["Bill",], "family": "Smith"}], "birthdate": "1980-01-01"},
            {"name": [{"given": ["John",], "family": "Smith"}], "birthdate": "1980-01-01"},
            {"name": [{"given": ["John",], "family": "Smith"}], "birthdate": "1985-11-12"},
        ]
        for datum in data:
            simple_mpi.insert_matched_patient(session, datum)

    def test_match_on_birthdate(self, session, prime_index):
        data = {"name": [{"given": ["Johnathon", "Bill",], "family": "Smith"}], "birthdate": "01/01/1980"}
        algo_config = {"blocks": [{"value": "birthdate"}]}
        matches = simple_mpi.get_block_data(session, data, algo_config)
        assert len(matches) == 4
        data = {"name": [{"given": ["Johnathon", "Bill",], "family": "Smith"}], "birthdate": "11/12/1985"}
        matches = simple_mpi.get_block_data(session, data, algo_config)
        assert len(matches) == 1

    def test_match_on_first_name(self, session, prime_index):
        data = {"name": [{"given": ["Johnathon", "Bill",], "family": "Smith"}], "birthdate": "01/01/1980"}
        algo_config = {"blocks": [{"value": "first_name"}]}
        matches = simple_mpi.get_block_data(session, data, algo_config)
        assert len(matches) == 5

    def test_match_on_birthdate_and_first_name(self, session, prime_index):
        data = {"name": [{"given": ["Johnathon", "Bill",], "family": "Smith"}], "birthdate": "01/01/1980"}
        algo_config = {"blocks": [{"value": "birthdate"}, {"value": "first_name"}]}
        matches = simple_mpi.get_block_data(session, data, algo_config)
        assert len(matches) == 4

    def test_match_on_birthdate_first_name_and_last_name(self, session, prime_index):
        data = {"name": [{"given": ["Johnathon", "Bill",], "family": "Smith"}], "birthdate": "01/01/1980"}
        algo_config = {"blocks": [{"value": "birthdate"}, {"value": "first_name"}, {"value": "last_name"}]}
        matches = simple_mpi.get_block_data(session, data, algo_config)
        assert len(matches) == 3
        data = {"name": [{"given": ["Billy",], "family": "Smitty"}], "birthdate": "Jan 1 1980"}
        matches = simple_mpi.get_block_data(session, data, algo_config)
        assert len(matches) == 2
        data = {"name": [{"given": ["Johnathon", "Bill",], "family": "Doeherty"}], "birthdate": "Jan 1 1980"}
        matches = simple_mpi.get_block_data(session, data, algo_config)
        assert len(matches) == 0

    def test_match_on_multiple_names(self, session, prime_index):
        data = {"name": [{"use": "official", "given": ["John", "Doe"], "family": "Smith"}, {"use": "maiden", "given": ["John"], "family": "Doe"}]}
        algo_config = {"blocks": [{"value": "first_name"}, {"value": "last_name"}]}
        matches = simple_mpi.get_block_data(session, data, algo_config)
        assert len(matches) == 4

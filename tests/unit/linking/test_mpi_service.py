"""
unit.linking.test_mpi_service.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.linking.mpi_service module.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy import orm

from recordlinker import models
from recordlinker.config import settings
from recordlinker.linking import mpi_service


@pytest.fixture(scope="function")
def session():
    engine = create_engine(settings.test_db_uri)
    models.Base.metadata.create_all(engine)  # Create all tables in the in-memory database

    # Create a new session factory and scoped session
    Session = orm.scoped_session(orm.sessionmaker(bind=engine))
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
        new_patient.data = {"name": []}
        assert mpi_service.insert_blocking_keys(session, new_patient) == []

    def test_patient_with_blocking_keys(self, session, new_patient):
        new_patient.data = {"name": [{"given": ["Johnathon", "Bill",], "family": "Smith"}], "birth_date": "01/01/1980"}
        keys = mpi_service.insert_blocking_keys(session, new_patient)
        assert len(keys) == 4
        for key in keys:
            assert keys[0].patient_id == new_patient.id
            if key.blockingkey == models.BlockingKey.BIRTHDATE.id:
                assert key.value == "1980-01-01"
            elif key.blockingkey == models.BlockingKey.FIRST_NAME.id:
                assert key.value in ["John", "Bill"]
            elif key.blockingkey == models.BlockingKey.LAST_NAME.id:
                assert key.value == "Smit"
            else:
                assert False, f"Unexpected blocking key: {key.blockingkey}"


class TestInsertPatient:
    def test_no_person(self, session):
        data = {"name": [{"given": ["Johnathon", "Bill",], "family": "Smith"}], "birth_date": "01/01/1980"}
        record = models.PIIRecord(**data)
        patient = mpi_service.insert_patient(session, record)
        assert patient.person_id is not None
        assert patient.data["birth_date"] == "1980-01-01"
        assert patient.data["name"] == [{"given": ["Johnathon", "Bill",], "family": "Smith"}]
        assert patient.external_person_id is None
        assert patient.external_person_source is None
        assert patient.person.internal_id is not None
        assert patient.person.id == patient.person_id
        assert len(patient.blocking_values) == 4

    def test_no_person_with_external_id(self, session):
        data = {"name": [{"given": ["Johnathon",], "family": "Smith"}], "birth_date": "01/01/1980"}
        record = models.PIIRecord(**data)
        patient = mpi_service.insert_patient(session, record, external_person_id="123456")
        assert patient.person_id is not None
        assert patient.data["birth_date"] == "1980-01-01"
        assert patient.data["name"] == [{"given": ["Johnathon",], "family": "Smith"}]
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
        data = {"name": [{"given": ["George",], "family": "Harrison"}], "birth_date": "1943-2-25"}
        record = models.PIIRecord(**data)
        patient = mpi_service.insert_patient(session, record, person=person)
        assert patient.person_id == person.id
        assert patient.data["birth_date"] == "1943-02-25"
        assert patient.data["name"] == [{"given": ["George",], "family": "Harrison"}]
        assert patient.external_person_id is None
        assert patient.external_person_source is None
        assert len(patient.blocking_values) == 3

    def test_with_person_and_external_patient_id(self, session):
        person = models.Person()
        session.add(person)
        session.flush()
        data = {"name": [{"given": ["George",], "family": "Harrison"}]}
        record = models.PIIRecord(**data)
        patient = mpi_service.insert_patient(session, record, person=person, external_patient_id="abc")
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
            {"name": [{"given": ["Johnathon", "Bill",], "family": "Smith"}], "birth_date": "01/01/1980"},
            {"name": [{"given": ["George",], "family": "Harrison"}], "birth_date": "1943-2-25"},
            {"name": [{"given": ["John",], "family": "Doe"}, {"given": ["John"], "family": "Lewis"}], "birth_date": "1980-01-01"},
            {"name": [{"given": ["Bill",], "family": "Smith"}], "birth_date": "1980-01-01"},
            {"name": [{"given": ["John",], "family": "Smith"}], "birth_date": "1980-01-01"},
            {"name": [{"given": ["John",], "family": "Smith"}], "birth_date": "1985-11-12"},
            {"name": [{"given": ["Ferris",], "family": "Bueller"}], "birth_date": ""},
        ]
        for datum in data:
            mpi_service.insert_patient(session, models.PIIRecord(**datum))

    def test_block_invalid_key(self, session):
        data = {"name": [{"given": ["Johnathon", "Bill",], "family": "Smith"}]}
        algo_config = {"blocks": [{"value": "unknown"}]}
        with pytest.raises(ValueError):
            mpi_service.get_block_data(session, models.PIIRecord(**data), algo_config)

    def test_block_missing_data(self, session, prime_index):
        data = {"name": [{"given": ["Johnathon", "Bill",], "family": "Smith"}]}
        algo_config = {"blocks": [{"value": "birthdate"}]}
        matches = mpi_service.get_block_data(session, models.PIIRecord(**data), algo_config)
        assert len(matches) == 0

    def test_block_empty_block_key(self, session, prime_index):
        data = {"name": [{"given": ["Ferris",], "family": "Bueller"}], "birth_date": ""}
        algo_config = {"blocks": [{"value": "birthdate"}, {"value": "first_name"}]}
        matches = mpi_service.get_block_data(session, models.PIIRecord(**data), algo_config)
        assert len(matches) == 0

    def test_block_on_birthdate(self, session, prime_index):
        data = {"name": [{"given": ["Johnathon", "Bill",], "family": "Smith"}], "birth_date": "01/01/1980"}
        algo_config = {"blocks": [{"value": "birthdate"}]}
        matches = mpi_service.get_block_data(session, models.PIIRecord(**data), algo_config)
        assert len(matches) == 4
        data = {"name": [{"given": ["Johnathon", "Bill",], "family": "Smith"}], "birth_date": "11/12/1985"}
        matches = mpi_service.get_block_data(session, models.PIIRecord(**data), algo_config)
        assert len(matches) == 1

    def test_block_on_first_name(self, session, prime_index):
        data = {"name": [{"given": ["Johnathon", "Bill",], "family": "Smith"}], "birth_date": "01/01/1980"}
        algo_config = {"blocks": [{"value": "first_name"}]}
        matches = mpi_service.get_block_data(session, models.PIIRecord(**data), algo_config)
        assert len(matches) == 5

    def test_block_on_birthdate_and_first_name(self, session, prime_index):
        data = {"name": [{"given": ["Johnathon", "Bill",], "family": "Smith"}], "birth_date": "01/01/1980"}
        algo_config = {"blocks": [{"value": "birthdate"}, {"value": "first_name"}]}
        matches = mpi_service.get_block_data(session, models.PIIRecord(**data), algo_config)
        assert len(matches) == 4

    def test_block_on_birthdate_first_name_and_last_name(self, session, prime_index):
        data = {"name": [{"given": ["Johnathon", "Bill",], "family": "Smith"}], "birth_date": "01/01/1980"}
        algo_config = {"blocks": [{"value": "birthdate"}, {"value": "first_name"}, {"value": "last_name"}]}
        matches = mpi_service.get_block_data(session, models.PIIRecord(**data), algo_config)
        assert len(matches) == 3
        data = {"name": [{"given": ["Billy",], "family": "Smitty"}], "birth_date": "Jan 1 1980"}
        matches = mpi_service.get_block_data(session, models.PIIRecord(**data), algo_config)
        assert len(matches) == 2
        data = {"name": [{"given": ["Johnathon", "Bill",], "family": "Doeherty"}], "birth_date": "Jan 1 1980"}
        matches = mpi_service.get_block_data(session, models.PIIRecord(**data), algo_config)
        assert len(matches) == 0

    def test_block_on_multiple_names(self, session, prime_index):
        data = {"name": [{"use": "official", "given": ["John", "Doe"], "family": "Smith"}, {"use": "maiden", "given": ["John"], "family": "Doe"}]}
        algo_config = {"blocks": [{"value": "first_name"}, {"value": "last_name"}]}
        matches = mpi_service.get_block_data(session, models.PIIRecord(**data), algo_config)
        assert len(matches) == 4

    def test_block_missing_keys(self, session, prime_index):
        data = {"birth_date": "01/01/1980"}
        algo_config = {"blocks": [{"value": "birthdate"}, {"value": "last_name"}]}
        matches = mpi_service.get_block_data(session, models.PIIRecord(**data), algo_config)
        assert len(matches) == 0

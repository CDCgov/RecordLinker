"""
unit.database.test_mpi_service.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.database.mpi_service module.
"""

import uuid

import pytest
import sqlalchemy.exc
from conftest import count_queries
from conftest import db_dialect
from sqlalchemy.orm.session import Session

from recordlinker import models
from recordlinker import schemas
from recordlinker.database import mpi_service


class TestInsertBlockingValues:
    def new_patient(self, session, data=None):
        patient = models.Patient(person=models.Person(), data=(data or {}))
        session.add(patient)
        session.flush()
        return patient

    def test_no_values(self, session: Session):
        pat = self.new_patient(session, data={"name": []})
        mpi_service.insert_blocking_values(session, [pat])
        assert len(pat.blocking_values) == 0

    def test_patient(self, session: Session):
        pat = self.new_patient(
            session,
            data={
                "name": [
                    {
                        "given": [
                            "Johnathon",
                            "Bill",
                        ],
                        "family": "Smith",
                    }
                ],
                "birthdate": "1980-01-01",
            },
        )
        mpi_service.insert_blocking_values(session, [pat])
        values = pat.blocking_values
        assert len(values) == 3
        for val in values:
            assert values[0].patient_id == pat.id
            if val.blockingkey == models.BlockingKey.BIRTHDATE.id:
                assert val.value == "1980-01-01"
            elif val.blockingkey == models.BlockingKey.FIRST_NAME.id:
                assert val.value in ["john", "bill"]
            elif val.blockingkey == models.BlockingKey.LAST_NAME.id:
                assert val.value == "smit"
            else:
                assert False, f"Unexpected blocking key: {val.blockingkey}"

    def test_multiple_patients(self, session: Session):
        pat1 = self.new_patient(
            session,
            data={
                "name": [
                    {
                        "given": [
                            "Johnathon",
                            "Bill",
                        ],
                        "family": "Smith",
                    }
                ],
                "birthdate": "1980-01-01",
            },
        )
        pat2 = self.new_patient(
            session,
            data={
                "name": [
                    {
                        "given": [
                            "George",
                        ],
                        "family": "Harrison",
                    }
                ],
                "birthdate": "1943-2-25",
            },
        )
        mpi_service.insert_blocking_values(session, [pat1, pat2])
        assert len(pat1.blocking_values) == 3
        assert len(pat2.blocking_values) == 3

    def test_with_mismatched_records(self, session: Session):
        pat = self.new_patient(session, data={"name": []})
        with pytest.raises(ValueError):
            mpi_service.insert_blocking_values(session, [pat], [])

    def test_with_records(self, session: Session):
        pat = self.new_patient(
            session,
            data={
                "name": [
                    {
                        "given": [
                            "Johnathon",
                            "Bill",
                        ],
                        "family": "Smith",
                    }
                ],
                "birthdate": "1980-01-01",
            },
        )
        rec = schemas.PIIRecord(**pat.data)
        mpi_service.insert_blocking_values(session, [pat], [rec])
        values = pat.blocking_values
        assert len(values) == 3
        assert set(v.patient_id for v in values) == {pat.id}
        assert set(v.value for v in values) == {"1980-01-01", "john", "smit"}


class TestInsertPatient:
    def test_no_person(self, session: Session):
        data = {
            "name": [
                {
                    "given": [
                        "Johnathon",
                        "Bill",
                    ],
                    "family": "Smith",
                }
            ],
            "birthdate": "01/01/1980",
        }
        record = schemas.PIIRecord(**data)
        patient = mpi_service.insert_patient(session, record)
        assert patient.person_id is None
        assert patient.data["birth_date"] == "1980-01-01"
        assert patient.data["name"] == [
            {
                "given": [
                    "Johnathon",
                    "Bill",
                ],
                "family": "Smith",
            }
        ]
        assert patient.external_person_id is None
        assert patient.external_person_source is None
        assert patient.person_id is None
        assert len(patient.blocking_values) == 3

    def test_no_person_with_external_id(self, session: Session):
        data = {
            "name": [
                {
                    "given": [
                        "Johnathon",
                    ],
                    "family": "Smith",
                }
            ],
            "birthdate": "01/01/1980",
        }
        record = schemas.PIIRecord(**data)
        patient = mpi_service.insert_patient(session, record, external_person_id="123456")
        assert patient.person_id is None
        assert patient.data["birth_date"] == "1980-01-01"
        assert patient.data["name"] == [
            {
                "given": [
                    "Johnathon",
                ],
                "family": "Smith",
            }
        ]
        assert patient.external_person_id == "123456"
        assert patient.external_person_source == "IRIS"
        assert len(patient.blocking_values) == 3

    def test_with_person(self, session: Session):
        person = models.Person()
        session.add(person)
        session.flush()
        data = {
            "name": [
                {
                    "given": [
                        "George",
                    ],
                    "family": "Harrison",
                }
            ],
            "birthdate": "1943-2-25",
        }
        record = schemas.PIIRecord(**data)
        patient = mpi_service.insert_patient(session, record, person=person)
        assert patient.person_id == person.id
        assert patient.data["birth_date"] == "1943-02-25"
        assert patient.data["name"] == [
            {
                "given": [
                    "George",
                ],
                "family": "Harrison",
            }
        ]
        assert patient.external_person_id is None
        assert patient.external_person_source is None
        assert len(patient.blocking_values) == 3

    def test_with_person_and_external_patient_id(self, session: Session):
        person = models.Person()
        session.add(person)
        session.flush()
        data = {
            "name": [
                {
                    "given": [
                        "George",
                    ],
                    "family": "Harrison",
                }
            ]
        }
        record = schemas.PIIRecord(**data)
        patient = mpi_service.insert_patient(
            session, record, person=person, external_patient_id="abc"
        )
        assert patient.person_id == person.id
        assert patient.data == data
        assert patient.external_patient_id == "abc"
        assert patient.external_person_id is None
        assert patient.external_person_source is None
        assert len(patient.blocking_values) == 2


class TestBulkInsertPatients:
    @classmethod
    def setup_class(cls):
        if db_dialect() == "mysql":
            pytest.skip("Test skipped because the database dialect is MySQL")

    def test_empty(self, session: Session):
        assert mpi_service.bulk_insert_patients(session, []) == []

    def test_no_person(self, session: Session):
        rec = schemas.PIIRecord(**{"name": [{"given": ["Johnathon"], "family": "Smith"}]})
        patients = mpi_service.bulk_insert_patients(session, [rec], external_person_id="123456")
        assert len(patients) == 1
        assert patients[0].person_id is None
        assert patients[0].data == {"name": [{"given": ["Johnathon"], "family": "Smith"}]}
        assert patients[0].external_person_id == "123456"
        values = patients[0].blocking_values
        assert len(values) == 2
        assert set(v.value for v in values) == {"john", "smit"}

    def test_with_person(self, session: Session):
        person = models.Person()
        session.add(person)
        session.flush()
        rec1 = schemas.PIIRecord(
            **{"birthdate": "1950-01-01", "name": [{"given": ["George"], "family": "Harrison"}]}
        )
        rec2 = schemas.PIIRecord(
            **{
                "birthdate": "1950-01-01",
                "name": [{"given": ["George", "Harold"], "family": "Harrison"}],
            }
        )
        patients = mpi_service.bulk_insert_patients(
            session, [rec1, rec2], person=person, external_person_id="123456"
        )
        assert len(patients) == 2
        assert patients[0].person_id == person.id
        assert patients[1].person_id == person.id
        assert patients[0].data == {
            "birth_date": "1950-01-01",
            "name": [{"given": ["George"], "family": "Harrison"}],
        }
        assert patients[1].data == {
            "birth_date": "1950-01-01",
            "name": [{"given": ["George", "Harold"], "family": "Harrison"}],
        }
        assert patients[0].external_person_id == "123456"
        assert patients[1].external_person_id == "123456"
        assert len(patients[0].blocking_values) == 3
        assert set(v.value for v in patients[0].blocking_values) == {"1950-01-01", "geor", "harr"}
        assert len(patients[1].blocking_values) == 3
        assert set(v.value for v in patients[1].blocking_values) == {
            "1950-01-01",
            "geor",
            "harr",
        }


class TestBulkInsertPatientsMySQL:
    @classmethod
    def setup_class(cls):
        if db_dialect() != "mysql":
            pytest.skip("Test skipped because the database dialect is not MySQL")

    def test_error(self, session: Session):
        with pytest.raises(ValueError):
            assert mpi_service.bulk_insert_patients(session, [])


class TestUpdatePatient:
    def test_no_patient(self, session: Session):
        with pytest.raises(ValueError):
            mpi_service.update_patient(session, models.Patient(), schemas.PIIRecord())

    def test_update_record(self, session: Session):
        patient = models.Patient(person=models.Person(), data={"sex": "M"})
        session.add(patient)
        session.flush()
        session.add(
            models.BlockingValue(
                patient_id=patient.id, blockingkey=models.BlockingKey.SEX.id, value="M"
            )
        )
        record = schemas.PIIRecord(
            **{"name": [{"given": ["John"], "family": "Doe"}], "birthdate": "1980-01-01"}
        )
        patient = mpi_service.update_patient(session, patient, record=record)
        assert patient.data == {
            "name": [{"given": ["John"], "family": "Doe"}],
            "birth_date": "1980-01-01",
        }
        assert len(patient.blocking_values) == 3

    def test_update_person(self, session: Session):
        person = models.Person()
        session.add(person)
        patient = models.Patient()
        session.add(patient)
        session.flush()
        patient = mpi_service.update_patient(session, patient, person=person)
        assert patient.person_id == person.id

    def test_update_external_patient_id(self, session: Session):
        patient = models.Patient()
        session.add(patient)
        session.flush()

        patient = mpi_service.update_patient(session, patient, external_patient_id="123")
        assert patient.external_patient_id == "123"


class TestDeleteBlockingValuesForPatient:
    def test_no_values(self, session: Session):
        other_patient = models.Patient()
        session.add(other_patient)
        session.flush()
        session.add(
            models.BlockingValue(
                patient_id=other_patient.id,
                blockingkey=models.BlockingKey.FIRST_NAME.id,
                value="John",
            )
        )
        session.flush()
        patient = models.Patient()
        session.add(patient)
        session.flush()
        assert len(patient.blocking_values) == 0
        mpi_service.delete_blocking_values_for_patient(session, patient)
        assert len(patient.blocking_values) == 0

    def test_with_values(self, session: Session):
        patient = models.Patient()
        session.add(patient)
        session.flush()
        session.add(
            models.BlockingValue(
                patient_id=patient.id, blockingkey=models.BlockingKey.FIRST_NAME.id, value="John"
            )
        )
        session.add(
            models.BlockingValue(
                patient_id=patient.id, blockingkey=models.BlockingKey.LAST_NAME.id, value="Smith"
            )
        )
        session.flush()
        assert len(patient.blocking_values) == 2
        mpi_service.delete_blocking_values_for_patient(session, patient)
        assert len(patient.blocking_values) == 0


class TestBlockData:
    @pytest.fixture
    def prime_index(self, session: Session):
        person_1 = models.Person()
        person_2 = models.Person()
        session.add(person_1)
        session.add(person_2)
        session.flush()

        data = [
            (
                {
                    "name": [
                        {
                            "given": [
                                "Johnathon",
                                "Bill",
                            ],
                            "family": "Smith",
                        }
                    ],
                    "birthdate": "01/01/1980",
                },
                person_1,
            ),
            (
                {
                    "name": [
                        {
                            "given": [
                                "George",
                            ],
                            "family": "Harrison",
                        }
                    ],
                    "birthdate": "1943-2-25",
                },
                models.Person(),
            ),
            (
                {
                    "name": [
                        {
                            "given": [
                                "John",
                            ],
                            "family": "Doe",
                        },
                        {"given": ["John"], "family": "Lewis"},
                    ],
                    "birthdate": "1980-01-01",
                },
                models.Person(),
            ),
            (
                {
                    "name": [
                        {
                            "given": [
                                "Bill",
                            ],
                            "family": "Smith",
                        }
                    ],
                    "birthdate": "1980-01-01",
                },
                person_1,
            ),
            (
                {
                    "name": [
                        {
                            "given": [
                                "John",
                            ],
                            "family": "Smith",
                        }
                    ],
                    "birthdate": "1980-01-01",
                },
                person_1,
            ),
            (
                {
                    "name": [
                        {
                            "given": [
                                "John",
                            ],
                            "family": "Smith",
                        }
                    ],
                    "birthdate": "1985-11-12",
                },
                models.Person(),
            ),
            (
                {
                    "name": [
                        {
                            "given": [
                                "Ferris",
                            ],
                            "family": "Bueller",
                        }
                    ],
                    "birthdate": "",
                },
                person_2,
            ),
            (
                {
                    "name": [
                        {
                            "given": [
                                "Ferris",
                            ],
                            "family": "Bueller",
                        }
                    ],
                    "birthdate": "1974-11-07",
                },
                person_2,
            ),
            (
                {
                    "name": [
                        {
                            "given": [
                                "Ferris",
                            ],
                            "family": "Bueller",
                        }
                    ],
                    "birthdate": "1983-08-17",
                },
                person_2,
            ),
        ]
        for datum, person in data:
            mpi_service.insert_patient(session, schemas.PIIRecord(**datum), person=person)

    def test_block_invalid_key(self, session: Session):
        data = {
            "name": [
                {
                    "given": [
                        "Johnathon",
                        "Bill",
                    ],
                    "family": "Smith",
                }
            ]
        }
        # passing in a invalid id of -1 for a blocking key which should raise a value error
        algorithm_pass = models.AlgorithmPass(blocking_keys=["INVALID"])
        with pytest.raises(ValueError):
            mpi_service.BlockData.get(session, schemas.PIIRecord(**data), algorithm_pass, 0.3)

    def test_block_missing_data(self, session: Session, prime_index: None):
        data = {
            "name": [
                {
                    "given": [
                        "Johnathon",
                        "Bill",
                    ],
                    "family": "Smith",
                }
            ]
        }
        algorithm_pass = models.AlgorithmPass(blocking_keys=["BIRTHDATE"])
        matches = mpi_service.BlockData.get(session, schemas.PIIRecord(**data), algorithm_pass, 0.3)
        assert len(matches) == 0

    def test_block_empty_block_key(self, session: Session, prime_index: None):
        data = {
            "name": [
                {
                    "given": [
                        "Ferris",
                    ],
                    "family": "Bueller",
                }
            ],
            "birthdate": "",
        }
        algorithm_pass = models.AlgorithmPass(blocking_keys=["BIRTHDATE", "FIRST_NAME"])
        matches = mpi_service.BlockData.get(session, schemas.PIIRecord(**data), algorithm_pass, 0.3)
        assert len(matches) == 0

    def test_block_filter_mpi_candidates(self, session: Session, prime_index: None):
        """
        Tests filtering candidates returned from the MPI for either blocking
        agreement or missing information. Patients who are in pulled clusters
        but have wrong blocking fields should be eliminated from consideration.
        """
        data = {
            "name": [
                {
                    "given": [
                        "Ferris",
                    ],
                    "family": "Bueller",
                }
            ],
            "birthdate": "1974-11-07",
        }
        algorithm_pass = models.AlgorithmPass(blocking_keys=["BIRTHDATE", "FIRST_NAME"])
        # Will initially be 3 patients in this person cluster
        # One agrees on blocking, one has missing values, and one
        # is wrong, so we should throw away that one
        matches = mpi_service.BlockData.get(session, schemas.PIIRecord(**data), algorithm_pass, 0.3)
        assert len(matches) == 2

    def test_block_on_birthdate(self, session: Session, prime_index: None):
        data = {
            "name": [
                {
                    "given": [
                        "Johnathon",
                        "Bill",
                    ],
                    "family": "Smith",
                }
            ],
            "birthdate": "01/01/1980",
        }
        algorithm_pass = models.AlgorithmPass(blocking_keys=["BIRTHDATE"])

        matches = mpi_service.BlockData.get(session, schemas.PIIRecord(**data), algorithm_pass, 0.3)
        assert len(matches) == 4
        data = {
            "name": [
                {
                    "given": [
                        "Johnathon",
                        "Bill",
                    ],
                    "family": "Smith",
                }
            ],
            "birthdate": "11/12/1985",
        }
        matches = mpi_service.BlockData.get(session, schemas.PIIRecord(**data), algorithm_pass, 0.3)
        assert len(matches) == 1

    def test_block_on_first_name(self, session: Session, prime_index: None):
        data = {
            "name": [
                {
                    "given": [
                        "Johnathon",
                        "Bill",
                    ],
                    "family": "Smith",
                }
            ],
            "birthdate": "01/01/1980",
        }
        algorithm_pass = models.AlgorithmPass(blocking_keys=["FIRST_NAME"])
        matches = mpi_service.BlockData.get(session, schemas.PIIRecord(**data), algorithm_pass, 0.3)
        # One candidate in MPI person_1 is a Bill, will be ruled out
        assert len(matches) == 4

    def test_block_on_birthdate_and_first_name(self, session: Session, prime_index: None):
        data = {
            "name": [
                {
                    "given": [
                        "Johnathon",
                        "Bill",
                    ],
                    "family": "Smith",
                }
            ],
            "birthdate": "01/01/1980",
        }
        algorithm_pass = models.AlgorithmPass(blocking_keys=["BIRTHDATE", "FIRST_NAME"])
        matches = mpi_service.BlockData.get(session, schemas.PIIRecord(**data), algorithm_pass, 0.3)
        # One candidate in MPI person_1 is just a Bill, ruled out
        assert len(matches) == 3

    def test_block_on_birthdate_first_name_and_last_name(self, session: Session, prime_index: None):
        data = {
            "name": [
                {
                    "given": [
                        "Johnathon",
                        "Bill",
                    ],
                    "family": "Smith",
                }
            ],
            "birthdate": "01/01/1980",
        }
        algorithm_pass = models.AlgorithmPass(
            blocking_keys=["BIRTHDATE", "FIRST_NAME", "LAST_NAME"]
        )
        matches = mpi_service.BlockData.get(session, schemas.PIIRecord(**data), algorithm_pass, 0.3)
        # One person in MPI person_1 is just a Bill, ruled out
        assert len(matches) == 2
        data = {
            "name": [
                {
                    "given": [
                        "Billy",
                    ],
                    "family": "Smitty",
                }
            ],
            "birthdate": "Jan 1 1980",
        }
        matches = mpi_service.BlockData.get(session, schemas.PIIRecord(**data), algorithm_pass, 0.3)
        # Blocking uses feature_iter, which yields only the first `given` for a
        # single name object, so only the patient with 'Bill' is caught
        assert len(matches) == 1
        data = {
            "name": [
                {
                    "given": [
                        "Johnathon",
                        "Bill",
                    ],
                    "family": "Doeherty",
                }
            ],
            "birthdate": "Jan 1 1980",
        }
        matches = mpi_service.BlockData.get(session, schemas.PIIRecord(**data), algorithm_pass, 0.3)
        assert len(matches) == 0

    def test_block_missing_some_values(self, session: Session, prime_index: None):
        data = {
            "name": [
                {
                    "given": [
                        "Johnathon",
                        "Bill",
                    ],
                    "family": "",
                }
            ],
            "birthdate": "01/01/1980",
        }
        algorithm_pass = models.AlgorithmPass(
            blocking_keys=["BIRTHDATE", "FIRST_NAME", "LAST_NAME"],
            kwargs={
                "log_odds": {"FIRST_NAME": 6.8, "LAST_NAME": 6.3, "BIRTHDATE": 10.1},
            },
        )
        matches = mpi_service.BlockData.get(session, schemas.PIIRecord(**data), algorithm_pass, 0.3)
        assert len(matches) == 3

    def test_block_missing_too_many_values(self, session: Session, prime_index: None):
        data = {
            "name": [
                {
                    "given": [
                        "Johnathon",
                        "Bill",
                    ],
                    "family": "",
                }
            ],
            "birthdate": "01/01/1980",
        }
        algorithm_pass = models.AlgorithmPass(
            blocking_keys=["BIRTHDATE", "FIRST_NAME", "LAST_NAME"],
            kwargs={
                "log_odds": {"FIRST_NAME": 6.8, "LAST_NAME": 6.3, "BIRTHDATE": 10.1},
            },
        )
        matches = mpi_service.BlockData.get(session, schemas.PIIRecord(**data), algorithm_pass, 0.2)
        assert len(matches) == 0

    def test_block_on_multiple_names(self, session: Session, prime_index: None):
        data = {
            "name": [
                {"use": "official", "given": ["John", "Doe"], "family": "Smith"},
                {"use": "maiden", "given": ["John"], "family": "Doe"},
            ]
        }
        algorithm_pass = models.AlgorithmPass(
            id=1,
            algorithm_id=1,
            blocking_keys=["FIRST_NAME", "LAST_NAME"],
            evaluators={},
            kwargs={},
        )
        matches = mpi_service.BlockData.get(session, schemas.PIIRecord(**data), algorithm_pass, 0.3)
        # One of patients in MPI person_1 is a Bill, so is excluded
        assert len(matches) == 4

    def test_block_missing_keys(self, session: Session, prime_index: None):
        data = {"birthdate": "01/01/1980"}
        algorithm_pass = models.AlgorithmPass(blocking_keys=["BIRTHDATE", "LAST_NAME"])
        matches = mpi_service.BlockData.get(session, schemas.PIIRecord(**data), algorithm_pass, 0.3)
        assert len(matches) == 0

    def test_block_on_duplicates(self, session: Session):
        data = {
            "external_id": "d3ecb447-d05f-4ec1-8ef1-ce4bbda59a25",
            "birth_date": "1997-12-09",
            "sex": "F",
            "mrn": "7bb85f23-044b-1f92-3521-f2cf258601b0",
            "address": [
                {
                    "line": ["783 Cronin Stravenue"],
                    "city": "Los Angeles",
                    "state": "CA",
                    "postal_code": "90405",
                    "country": "US",
                    "latitude": 34.12688209447149,
                    "longitude": -118.56442326530481,
                    "extension": [
                        {
                            "url": "http://hl7.org/fhir/StructureDefinition/geolocation",
                            "extension": [
                                {"url": "latitude", "valueDecimal": 34.12688209447149},
                                {"url": "longitude", "valueDecimal": -118.56442326530481},
                            ],
                        }
                    ],
                }
            ],
            "name": [
                {
                    "family": "Rodr\u00edguez701",
                    "given": ["Lourdes258", "Blanca837"],
                    "use": "official",
                    "prefix": ["Ms."],
                }
            ],
            "phone": [{"system": "phone", "value": "555-401-5073", "use": "home"}],
        }
        mpi_service.insert_patient(session, schemas.PIIRecord(**data), models.Person(), 0.3)
        mpi_service.insert_patient(session, schemas.PIIRecord(**data), models.Person(), 0.3)
        mpi_service.insert_patient(session, schemas.PIIRecord(**data), models.Person(), 0.3)
        algorithm_pass = models.AlgorithmPass(
            blocking_keys=["FIRST_NAME", "LAST_NAME", "ZIP", "SEX"]
        )

        matches = mpi_service.BlockData.get(session, schemas.PIIRecord(**data), algorithm_pass, 0.3)
        assert len(matches) == 3


class TestGetPatientsByReferenceIds:
    def test_invalid_reference_id(self, session: Session):
        with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
            mpi_service.get_patients_by_reference_ids(session, "123")

    def test_reference_ids(self, session: Session):
        patient = models.Patient(person=models.Person(), data={})
        session.add(patient)
        session.flush()
        assert mpi_service.get_patients_by_reference_ids(
            session, uuid.uuid4(), patient.reference_id
        ) == [None, patient]

    def test_eager_load_of_person(self, session: Session):
        pat_ref = uuid.uuid4()
        per_ref = uuid.uuid4()
        person = models.Person(reference_id=per_ref)
        patient = models.Patient(person=person, reference_id=pat_ref, data={})
        session.add(patient)
        session.flush()
        session.expire(person)  # expiring the cache to fully test the query
        session.expire(patient)  # expiring the cache to fully test the query
        with count_queries(session) as qcount:
            pats = mpi_service.get_patients_by_reference_ids(session, pat_ref)
            assert patient == pats[0]
            assert per_ref == pats[0].person.reference_id
        # assert only one query was made
        assert qcount() == 1


class TestGetPersonByReferenceId:
    def test_invalid_reference_id(self, session: Session):
        with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
            mpi_service.get_person_by_reference_id(session, "123")

    def test_no_reference_id(self, session: Session):
        assert mpi_service.get_person_by_reference_id(session, uuid.uuid4()) is None

    def test_reference_id(self, session: Session):
        person = models.Person()
        session.add(person)
        session.flush()
        assert mpi_service.get_person_by_reference_id(session, person.reference_id) == person


class TestUpdatePersonCluster:
    def test_no_person(self, session: Session):
        person = models.Person()
        patient = models.Patient(person=person, data={})
        session.add(patient)
        session.flush()
        original_person_id = patient.person.id
        person = mpi_service.update_person_cluster(session, [patient])
        assert person.id != original_person_id

    def test_with_person(self, session: Session):
        patient = models.Patient(person=models.Person(), data={})
        session.add(patient)
        new_person = models.Person()
        session.add(new_person)
        session.flush()
        person = mpi_service.update_person_cluster(session, [patient], person=new_person)
        assert person.id == new_person.id

    def test_multiple_patients(self, session: Session):
        patient1 = models.Patient(person=models.Person(), data={})
        patient2 = models.Patient(person=models.Person(), data={})
        session.add_all([patient1, patient2])
        session.flush()
        person = mpi_service.update_person_cluster(session, [patient1, patient2])
        assert person.id == patient1.person.id
        assert person.id == patient2.person.id


class TestResetMPI:
    def test(self, session: Session):
        data = {
            "name": [
                {
                    "given": [
                        "Johnathon",
                        "Bill",
                    ],
                    "family": "Smith",
                }
            ],
            "birthdate": "1980-01-01",
        }
        mpi_service.insert_patient(session, schemas.PIIRecord(**data), person=models.Person())
        assert session.query(models.Patient).count() == 1
        assert session.query(models.Person).count() == 1
        assert session.query(models.BlockingValue).count() == 3
        mpi_service.reset_mpi(session)
        assert session.query(models.Patient).count() == 0
        assert session.query(models.Person).count() == 0
        assert session.query(models.BlockingValue).count() == 0


class TestUpdatePatientPersonIds:
    def test_invalid_person_id(self, session: Session):
        with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
            mpi_service.update_patient_person_ids(session, models.Person(), "123")

    def test_update_patient_person_ids(self, session: Session):
        # Tests that we can update the person_id of a patient
        person1 = models.Person()
        patient1 = models.Patient(person=person1, data={})
        person2 = models.Person()
        patient2 = models.Patient(person=person2, data={})
        session.add_all([patient1, patient2])
        session.flush()
        assert patient1.person_id != patient2.person_id
        mpi_service.update_patient_person_ids(session, person1, [patient2.person_id])
        assert patient1.person_id == patient2.person_id


class TestGetPersonsbyReferenceIds:
    def test_invalid_reference_id(self, session: Session):
        with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
            mpi_service.get_persons_by_reference_ids(session, "123")

    def test_reference_ids(self, session: Session):
        person = models.Person()
        session.add(person)
        session.flush()
        assert mpi_service.get_persons_by_reference_ids(
            session, uuid.uuid4(), person.reference_id
        ) == [None, person]


class TestDeletePersons:
    def test_delete_persons(self, session: Session):
        person1 = models.Person()
        person2 = models.Person()
        session.add_all([person1, person2])
        session.flush()
        assert session.query(models.Person).count() == 2
        mpi_service.delete_persons(session, [person1])
        assert session.query(models.Person).count() == 1
        assert mpi_service.get_person_by_reference_id(session, person1.reference_id) is None
        assert mpi_service.get_person_by_reference_id(session, person2.reference_id) == person2


class TestCheckPersonForPatients:
    def test_check_person_for_patients(self, session: Session):
        person1 = models.Person()
        patient1 = models.Patient(person=person1, data={})
        person2 = models.Person()
        patient2 = models.Patient(person=person2, data={})
        session.add_all([patient1, patient2])
        session.flush()
        session.delete(patient2)

        assert session.query(models.Patient).count() == 1
        assert session.query(models.Person).count() == 2
        assert mpi_service.check_person_for_patients(session, person1)
        assert not mpi_service.check_person_for_patients(session, person2)


class TestGetOrphanedPatients:
    def test_get_orphaned_patients_success(self, session: Session):
        patient = models.Patient(person=None, data={"reference_id": str(uuid.uuid4())})
        patient2 = models.Patient(person=models.Person(), data={})
        session.add_all([patient, patient2])
        session.flush()
        assert session.query(models.Patient).count() == 2
        assert session.query(models.Person).count() == 1
        assert mpi_service.get_orphaned_patients(session) == [patient]

    def test_get_orphaned_patients_no_patients(self, session: Session):
        person = models.Person()
        patient = models.Patient(person=person, data={})
        session.add(patient)
        session.flush()
        assert mpi_service.get_orphaned_patients(session) == []

    def test_get_orphaned_patients_limit(self, session: Session):
        # Checks that limit is correctly applied
        patient1 = models.Patient(person=None, data={"id": 1, "reference_id": str(uuid.uuid4())})
        patient2 = models.Patient(person=None, data={"id": 2, "reference_id": str(uuid.uuid4())})
        patient3 = models.Patient(person=models.Person(), data={})
        session.add_all([patient1, patient2, patient3])
        session.flush()

        assert len(mpi_service.get_orphaned_patients(session, limit=1)) == 1
        assert len(mpi_service.get_orphaned_patients(session, limit=2)) == 2
        assert len(mpi_service.get_orphaned_patients(session, limit=3)) == 2

    def test_get_orphaned_patients_cursor(self, session: Session):
        patient1 = models.Patient(person=None, data={"id": 1})
        patient2 = models.Patient(person=None, data={"id": 2})
        patient3 = models.Patient(person=None, data={"id": 3})
        patient4 = models.Patient(person=models.Person(), id=4)
        session.add_all([patient1, patient2, patient3, patient4])
        session.flush()

        # Checks that cursor is correctly applied
        assert mpi_service.get_orphaned_patients(session, limit=1, cursor=patient1.data["id"]) == [
            patient2
        ]

        assert mpi_service.get_orphaned_patients(session, limit=1, cursor=patient2.data["id"]) == [
            patient3
        ]
        assert mpi_service.get_orphaned_patients(session, limit=2, cursor=patient2.data["id"]) == [
            patient3
        ]
        assert mpi_service.get_orphaned_patients(session, limit=2, cursor=patient1.data["id"]) == [
            patient2,
            patient3,
        ]


class TestGetOrphanedPersons:
    def test_get_orphaned_persons_success(self, session: Session):
        person1 = models.Person()
        person2 = models.Person()
        patient1 = models.Patient(person=person1, data={})
        session.add_all([patient1, person2])
        session.flush()
        assert session.query(models.Patient).count() == 1
        assert session.query(models.Person).count() == 2
        assert mpi_service.get_orphaned_persons(session) == [person2]

    def test_get_orphaned_persons_no_persons(self, session: Session):
        patient = models.Patient(person=models.Person(), data={})
        session.add(patient)
        session.flush()
        assert mpi_service.get_orphaned_persons(session) == []

    def test_get_orphaned_persons_limit(self, session: Session):
        # Checks that limit is correctly applied
        person1 = models.Person()
        person2 = models.Person()
        person3 = models.Person()
        patient = models.Patient(person=person1, data={})
        session.add_all([patient, person2, person3])
        session.flush()

        assert len(mpi_service.get_orphaned_persons(session, limit=1)) == 1
        assert len(mpi_service.get_orphaned_persons(session, limit=2)) == 2
        assert len(mpi_service.get_orphaned_persons(session, limit=3)) == 2

    def test_get_orphaned_persons_cursor(self, session: Session):
        # Checks that cursor is correctly applied
        person1 = models.Person(id=1)
        person2 = models.Person(id=2)
        person3 = models.Person(id=3)
        person4 = models.Person(id=4)
        patient = models.Patient(person=person4, data={})
        session.add_all([patient, person1, person2, person3])
        session.flush()

        assert mpi_service.get_orphaned_persons(session, limit=1, cursor=person1.id) == [person2]
        assert mpi_service.get_orphaned_persons(session, limit=1, cursor=person2.id) == [person3]
        assert mpi_service.get_orphaned_persons(session, limit=2, cursor=person2.id) == [person3]
        assert mpi_service.get_orphaned_persons(session, limit=2, cursor=person1.id) == [
            person2,
            person3,
        ]
        assert mpi_service.get_orphaned_persons(session, limit=5, cursor=person1.id) == [
            person2,
            person3,
        ]

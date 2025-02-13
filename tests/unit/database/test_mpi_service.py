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

from recordlinker import models
from recordlinker import schemas
from recordlinker.database import mpi_service


class TestInsertBlockingValues:
    def new_patient(self, session, data=None):
        patient = models.Patient(person=models.Person(), data=(data or {}))
        session.add(patient)
        session.flush()
        return patient

    def test_no_values(self, session):
        pat = self.new_patient(session, data={"name": []})
        mpi_service.insert_blocking_values(session, [pat])
        assert len(pat.blocking_values) == 0

    def test_patient(self, session):
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
                assert val.value in ["John", "Bill"]
            elif val.blockingkey == models.BlockingKey.LAST_NAME.id:
                assert val.value == "Smit"
            else:
                assert False, f"Unexpected blocking key: {val.blockingkey}"

    def test_multiple_patients(self, session):
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

    def test_with_mismatched_records(self, session):
        pat = self.new_patient(session, data={"name": []})
        with pytest.raises(ValueError):
            mpi_service.insert_blocking_values(session, [pat], [])

    def test_with_records(self, session):
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
        assert set(v.value for v in values) == {"1980-01-01", "John", "Smit"}


class TestInsertPatient:
    def test_no_person(self, session):
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

    def test_no_person_with_external_id(self, session):
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

    def test_with_person(self, session):
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

    def test_with_person_and_external_patient_id(self, session):
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

    def test_empty(self, session):
        assert mpi_service.bulk_insert_patients(session, []) == []

    def test_no_person(self, session):
        rec = schemas.PIIRecord(**{"name": [{"given": ["Johnathon"], "family": "Smith"}]})
        patients = mpi_service.bulk_insert_patients(session, [rec], external_person_id="123456")
        assert len(patients) == 1
        assert patients[0].person_id is None
        assert patients[0].data == {"name": [{"given": ["Johnathon"], "family": "Smith"}]}
        assert patients[0].external_person_id == "123456"
        values = patients[0].blocking_values
        assert len(values) == 2
        assert set(v.value for v in values) == {"John", "Smit"}

    def test_with_person(self, session):
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
        assert set(v.value for v in patients[0].blocking_values) == {"1950-01-01", "Geor", "Harr"}
        assert len(patients[1].blocking_values) == 3
        assert set(v.value for v in patients[1].blocking_values) == {
            "1950-01-01",
            "Geor",
            "Harr",
        }


class TestBulkInsertPatientsMySQL:
    @classmethod
    def setup_class(cls):
        if db_dialect() != "mysql":
            pytest.skip("Test skipped because the database dialect is not MySQL")

    def test_error(self, session):
        with pytest.raises(ValueError):
            assert mpi_service.bulk_insert_patients(session, [])


class TestUpdatePatient:
    def test_no_patient(self, session):
        with pytest.raises(ValueError):
            mpi_service.update_patient(session, models.Patient(), schemas.PIIRecord())

    def test_update_record(self, session):
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

    def test_update_person(self, session):
        person = models.Person()
        session.add(person)
        patient = models.Patient()
        session.add(patient)
        session.flush()
        patient = mpi_service.update_patient(session, patient, person=person)
        assert patient.person_id == person.id

    def test_update_external_patient_id(self, session):
        patient = models.Patient()
        session.add(patient)
        session.flush()

        patient = mpi_service.update_patient(session, patient, external_patient_id="123")
        assert patient.external_patient_id == "123"


class TestDeleteBlockingValuesForPatient:
    def test_no_values(self, session):
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

    def test_with_values(self, session):
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


class TestGetBlockData:
    @pytest.fixture
    def prime_index(self, session):
        person_1 = models.Person()
        session.add(person_1)
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
                models.Person(),
            ),
        ]
        for datum, person in data:
            mpi_service.insert_patient(session, schemas.PIIRecord(**datum), person=person)

    def test_block_invalid_key(self, session):
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
            mpi_service.get_block_data(session, schemas.PIIRecord(**data), algorithm_pass)

    def test_block_missing_data(self, session, prime_index):
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
        matches = mpi_service.get_block_data(session, schemas.PIIRecord(**data), algorithm_pass)
        assert len(matches) == 0

    def test_block_empty_block_key(self, session, prime_index):
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
        matches = mpi_service.get_block_data(session, schemas.PIIRecord(**data), algorithm_pass)
        assert len(matches) == 0

    def test_block_on_birthdate(self, session, prime_index):
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

        matches = mpi_service.get_block_data(session, schemas.PIIRecord(**data), algorithm_pass)
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
        matches = mpi_service.get_block_data(session, schemas.PIIRecord(**data), algorithm_pass)
        assert len(matches) == 1

    def test_block_on_first_name(self, session, prime_index):
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
        matches = mpi_service.get_block_data(session, schemas.PIIRecord(**data), algorithm_pass)
        assert len(matches) == 5

    def test_block_on_birthdate_and_first_name(self, session, prime_index):
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
        matches = mpi_service.get_block_data(session, schemas.PIIRecord(**data), algorithm_pass)
        assert len(matches) == 4

    def test_block_on_birthdate_first_name_and_last_name(self, session, prime_index):
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
        matches = mpi_service.get_block_data(session, schemas.PIIRecord(**data), algorithm_pass)
        assert len(matches) == 3
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
        matches = mpi_service.get_block_data(session, schemas.PIIRecord(**data), algorithm_pass)
        assert len(matches) == 3
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
        matches = mpi_service.get_block_data(session, schemas.PIIRecord(**data), algorithm_pass)
        assert len(matches) == 0

    def test_block_on_multiple_names(self, session, prime_index):
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
            rule="",
            kwargs={},
        )
        matches = mpi_service.get_block_data(session, schemas.PIIRecord(**data), algorithm_pass)
        assert len(matches) == 5

    def test_block_missing_keys(self, session, prime_index):
        data = {"birthdate": "01/01/1980"}
        algorithm_pass = models.AlgorithmPass(blocking_keys=["BIRTHDATE", "LAST_NAME"])
        matches = mpi_service.get_block_data(session, schemas.PIIRecord(**data), algorithm_pass)
        assert len(matches) == 0

    def test_block_on_duplicates(self, session):
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
        mpi_service.insert_patient(session, schemas.PIIRecord(**data), models.Person())
        mpi_service.insert_patient(session, schemas.PIIRecord(**data), models.Person())
        mpi_service.insert_patient(session, schemas.PIIRecord(**data), models.Person())
        algorithm_pass = models.AlgorithmPass(
            blocking_keys=["FIRST_NAME", "LAST_NAME", "ZIP", "SEX"]
        )

        matches = mpi_service.get_block_data(session, schemas.PIIRecord(**data), algorithm_pass)
        assert len(matches) == 3


class TestGetPatientsByReferenceIds:
    def test_invalid_reference_id(self, session):
        with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
            mpi_service.get_patients_by_reference_ids(session, "123")

    def test_reference_ids(self, session):
        patient = models.Patient(person=models.Person(), data={})
        session.add(patient)
        session.flush()
        assert mpi_service.get_patients_by_reference_ids(
            session, uuid.uuid4(), patient.reference_id
        ) == [None, patient]

    def test_eager_load_of_person(self, session):
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
    def test_invalid_reference_id(self, session):
        with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
            mpi_service.get_person_by_reference_id(session, "123")

    def test_no_reference_id(self, session):
        assert mpi_service.get_person_by_reference_id(session, uuid.uuid4()) is None

    def test_reference_id(self, session):
        person = models.Person()
        session.add(person)
        session.flush()
        assert mpi_service.get_person_by_reference_id(session, person.reference_id) == person


class TestUpdatePersonCluster:
    def test_no_person(self, session):
        person = models.Person()
        patient = models.Patient(person=person, data={})
        session.add(patient)
        session.flush()
        original_person_id = patient.person.id
        person = mpi_service.update_person_cluster(session, [patient])
        assert person.id != original_person_id

    def test_with_person(self, session):
        patient = models.Patient(person=models.Person(), data={})
        session.add(patient)
        new_person = models.Person()
        session.add(new_person)
        session.flush()
        person = mpi_service.update_person_cluster(session, [patient], person=new_person)
        assert person.id == new_person.id

    def test_multiple_patients(self, session):
        patient1 = models.Patient(person=models.Person(), data={})
        patient2 = models.Patient(person=models.Person(), data={})
        session.add_all([patient1, patient2])
        session.flush()
        person = mpi_service.update_person_cluster(session, [patient1, patient2])
        assert person.id == patient1.person.id
        assert person.id == patient2.person.id


class TestResetMPI:
    def test(self, session):
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
    def test_invalid_person_id(self, session):
        with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
            mpi_service.update_patient_person_ids(session, models.Person(), "123")

    def test_update_patient_person_ids(self, session):
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
    def test_invalid_reference_id(self, session):
        with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
            mpi_service.get_persons_by_reference_ids(session, "123")

    def test_reference_ids(self, session):
        person = models.Person()
        session.add(person)
        session.flush()
        assert mpi_service.get_persons_by_reference_ids(
            session, uuid.uuid4(), person.reference_id
        ) == [None, person]


class TestDeletePersons:
    def test_delete_persons(self, session):
        person1 = models.Person()
        person2 = models.Person()
        session.add_all([person1, person2])
        session.flush()
        assert session.query(models.Person).count() == 2
        mpi_service.delete_persons(session, [person1])
        assert session.query(models.Person).count() == 1
        assert mpi_service.get_person_by_reference_id(session, person1.reference_id) is None
        assert mpi_service.get_person_by_reference_id(session, person2.reference_id) == person2

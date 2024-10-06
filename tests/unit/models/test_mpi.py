"""
unit.models.test_mpi.py
~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.models.mpi module.
"""

import datetime

import pytest

from recordlinker import models
from recordlinker.schemas import pii


class TestPatient:
    def test_record_setter(self):
        patient = models.Patient()
        with pytest.raises(AssertionError):
            patient.record = "invalid"
        patient.record = pii.PIIRecord()
        assert patient.data == {}
        patient.record = pii.PIIRecord(birthDate="1980-01-01", sex="male")
        assert patient.data == {"birth_date": "1980-01-01", "sex": "M"}
        patient.record = pii.PIIRecord(birthDate="1980-01-01", sex="male", mrn="", name=[])
        assert patient.data == {"birth_date": "1980-01-01", "sex": "M", "mrn": ""}


class TestBlockingKey:
    def test_extract_birthdate(self):
        rec = pii.PIIRecord(**{"dob": "01/01/1980"})
        assert models.BlockingKey.BIRTHDATE.to_value(rec) == set()
        rec = pii.PIIRecord(**{"birth_date": "1980-01-01"})
        assert models.BlockingKey.BIRTHDATE.to_value(rec) == {"1980-01-01"}
        rec = pii.PIIRecord(**{"birthdate": datetime.date(1980, 1, 1)})
        assert models.BlockingKey.BIRTHDATE.to_value(rec) == {"1980-01-01"}
        rec = pii.PIIRecord(**{"birthDate": "01/01/1980"})
        assert models.BlockingKey.BIRTHDATE.to_value(rec) == {"1980-01-01"}
        rec = pii.PIIRecord(**{"birthDate": ""})
        assert models.BlockingKey.BIRTHDATE.to_value(rec) == set()

    def test_extract_mrn_last_four(self):
        rec = pii.PIIRecord(**{"ssn": "123456789"})
        assert models.BlockingKey.MRN.to_value(rec) == set()
        rec = pii.PIIRecord(**{"mrn": None})
        assert models.BlockingKey.MRN.to_value(rec) == set()
        rec = pii.PIIRecord(**{"mrn": "123456789"})
        assert models.BlockingKey.MRN.to_value(rec) == {"6789"}
        rec = pii.PIIRecord(**{"mrn": "89"})
        assert models.BlockingKey.MRN.to_value(rec) == {"89"}

    def test_extract_sex(self):
        rec = pii.PIIRecord(**{"gender": "M"})
        assert models.BlockingKey.SEX.to_value(rec) == set()
        rec = pii.PIIRecord(**{"sex": ""})
        assert models.BlockingKey.SEX.to_value(rec) == set()
        rec = pii.PIIRecord(**{"sex": "M"})
        assert models.BlockingKey.SEX.to_value(rec) == {"M"}
        rec = pii.PIIRecord(**{"sex": "Male"})
        assert models.BlockingKey.SEX.to_value(rec) == {"M"}
        rec = pii.PIIRecord(**{"sex": "f"})
        assert models.BlockingKey.SEX.to_value(rec) == {"F"}
        rec = pii.PIIRecord(**{"sex": "FEMALE"})
        assert models.BlockingKey.SEX.to_value(rec) == {"F"}
        rec = pii.PIIRecord(**{"sex": "other"})
        assert models.BlockingKey.SEX.to_value(rec) == {"U"}
        rec = pii.PIIRecord(**{"sex": "unknown"})
        assert models.BlockingKey.SEX.to_value(rec) == {"U"}
        rec = pii.PIIRecord(**{"sex": "?"})
        assert models.BlockingKey.SEX.to_value(rec) == {"U"}

    def test_extract_zipcode(self):
        rec = pii.PIIRecord(**{"zip_code": "12345"})
        assert models.BlockingKey.ZIP.to_value(rec) == set()
        rec = pii.PIIRecord(**{"address": [{"postalCode": None}]})
        assert models.BlockingKey.ZIP.to_value(rec) == set()
        rec = pii.PIIRecord(**{"address": [{"zipcode": "12345"}]})
        assert models.BlockingKey.ZIP.to_value(rec) == {"12345"}
        rec = pii.PIIRecord(**{"address": [{"postal_code": "12345-6789"}]})
        assert models.BlockingKey.ZIP.to_value(rec) == {"12345"}
        rec = pii.PIIRecord(**{"address": [{"zipCode": "12345-6789"}, {"zip": "54321"}]})
        assert models.BlockingKey.ZIP.to_value(rec) == {"12345", "54321"}

    def test_extract_first_name_first_four(self):
        rec = pii.PIIRecord(**{"first_name": "John"})
        assert models.BlockingKey.FIRST_NAME.to_value(rec) == set()
        rec = pii.PIIRecord(**{"name": [{"given": [""], "family": "Doe"}]})
        assert models.BlockingKey.FIRST_NAME.to_value(rec) == set()
        rec = pii.PIIRecord(**{"name": [{"given": ["John", "Jane"], "family": "Doe"}]})
        assert models.BlockingKey.FIRST_NAME.to_value(rec) == {"John", "Jane"}
        rec = pii.PIIRecord(**{
            "name": [
                {"given": ["Janet", "Johnathon"], "family": "Doe"},
                {"given": ["Jane"], "family": "Smith"},
            ]
        })
        assert models.BlockingKey.FIRST_NAME.to_value(rec) == {"Jane", "John"}

    def test_extract_last_name_first_four(self):
        rec = pii.PIIRecord(**{"last_name": "Doe"})
        assert models.BlockingKey.LAST_NAME.to_value(rec) == set()
        rec = pii.PIIRecord(**{"name": [{"family": ""}]})
        assert models.BlockingKey.LAST_NAME.to_value(rec) == set()
        rec = pii.PIIRecord(**{"name": [{"family": "Doe"}]})
        assert models.BlockingKey.LAST_NAME.to_value(rec) == {"Doe"}
        rec = pii.PIIRecord(**{"name": [{"family": "Smith"}, {"family": "Doe"}]})
        assert models.BlockingKey.LAST_NAME.to_value(rec) == {"Smit", "Doe"}

    def test_extract_address_first_four(self):
        rec = pii.PIIRecord(**{"line": "123 Main St"})
        assert models.BlockingKey.ADDRESS.to_value(rec) == set()
        rec = pii.PIIRecord(**{"address": [{"line": ["123 Main St"]}]})
        assert models.BlockingKey.ADDRESS.to_value(rec) == {"123 "}
        rec = pii.PIIRecord(**{"address": [{"line": ["123 Main St", "Apt 2"]}]})
        assert models.BlockingKey.ADDRESS.to_value(rec) == {"123 "}
        rec = pii.PIIRecord(**{"address": [{"line": ["123 Main St"]}, {"line": ["456 Elm St"]}]})
        assert models.BlockingKey.ADDRESS.to_value(rec) == {"123 ", "456 "}

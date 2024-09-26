"""
unit.models.test_pii.py
~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.models.pii module.
"""

import datetime
import uuid

import pydantic
import pytest

from recordlinker.models import pii as models


class TestPIIRecord:
    def test_parse_external_id(self):
        record = models.PIIRecord(
            external_id=uuid.UUID("7ca699d9-1986-4c0c-a0fd-ac4ae0dfa297")
        )
        assert record.external_id == "7ca699d9-1986-4c0c-a0fd-ac4ae0dfa297"
        record = models.PIIRecord(external_id=12345)
        assert record.external_id == "12345"
        record = models.PIIRecord(external_id="12345")
        assert record.external_id == "12345"
        record = models.PIIRecord()
        assert record.external_id is None

    def test_parse_birthdate(self):
        record = models.PIIRecord(birthDate="1980-01-01")
        assert record.birth_date == datetime.date(1980, 1, 1)
        record = models.PIIRecord(birthDate="January 1, 1980")
        assert record.birth_date == datetime.date(1980, 1, 1)
        record = models.PIIRecord(birth_date="Jan 1 1980")
        assert record.birth_date == datetime.date(1980, 1, 1)
        record = models.PIIRecord(birth_date="1/1/1980")
        assert record.birth_date == datetime.date(1980, 1, 1)
        record = models.PIIRecord()
        assert record.birth_date is None

    def test_parse_invalid_birthdate(self):
        with pytest.raises(pydantic.ValidationError):
            models.PIIRecord(birth_date="1 de enero de 1980")

    def test_parse_sex(self):
        record = models.PIIRecord(sex="M")
        assert record.sex == models.Sex.M
        record = models.PIIRecord(sex="m")
        assert record.sex == models.Sex.M
        record = models.PIIRecord(sex="Male")
        assert record.sex == models.Sex.M
        record = models.PIIRecord(sex="F")
        assert record.sex == models.Sex.F
        record = models.PIIRecord(sex="f")
        assert record.sex == models.Sex.F
        record = models.PIIRecord(sex="FEMALE")
        assert record.sex == models.Sex.F
        record = models.PIIRecord(sex="U")
        assert record.sex == models.Sex.U
        record = models.PIIRecord(sex="Unknown")
        assert record.sex == models.Sex.U
        record = models.PIIRecord()
        assert record.sex is None

    def test_field_iter(self):
        record = models.PIIRecord(
            external_id="99",
            birth_date="1980-2-1",
            sex="M",
            mrn="123456",
            address=[
                models.Address(
                    line=["123 Main St"],
                    city="Anytown",
                    state="NY",
                    postalCode="12345",
                    country="US",
                ),
                models.Address(
                    line=["456 Elm St"],
                    city="Somecity",
                    state="CA",
                    postal_code="98765-4321",
                    country="US",
                ),
            ],
            name=[
                models.Name(family="Doe", given=["John", "L"]),
                models.Name(family="Smith", given=["Jane"]),
            ],
            telecom=[
                models.Telecom(value="555-123-4567"),
                models.Telecom(value="555-987-6543"),
            ],
        )

        with pytest.raises(ValueError):
            list(record.field_iter("external_id"))

        assert list(record.field_iter(models.Feature.BIRTHDATE)) == ["1980-02-01"]
        assert list(record.field_iter(models.Feature.MRN)) == ["123456"]
        assert list(record.field_iter(models.Feature.SEX)) == ["m"]
        assert list(record.field_iter(models.Feature.ADDRESS)) == ["123 Main St", "456 Elm St"]
        assert list(record.field_iter(models.Feature.CITY)) == ["Anytown", "Somecity"]
        assert list(record.field_iter(models.Feature.STATE)) == ["NY", "CA"]
        assert list(record.field_iter(models.Feature.ZIPCODE)) == ["12345", "98765"]
        assert list(record.field_iter(models.Feature.FIRST_NAME)) == ["John", "L", "Jane"]
        assert list(record.field_iter(models.Feature.LAST_NAME)) == ["Doe", "Smith"]

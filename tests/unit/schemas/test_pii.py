"""
unit.schemas.test_pii.py
~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.schemas.pii module.
"""

import datetime
import unittest.mock
import uuid

import pydantic
import pytest

from recordlinker.models import BlockingKey
from recordlinker.schemas import pii


class TestPIIRecord:
    def test_model_construct(self):
        data = {
            "mrn": "99",
            "birth_date": "1980-2-1",
            "name": [
                {"family": "Doe", "given": ["John", "L"]},
                {"family": "Smith", "given": ["Jane"]},
            ],
            "address": [
                {
                    "line": ["123 Main St"],
                    "city": "Anytown",
                    "state": "NY",
                    "postalCode": "12345",
                    "country": "US",
                    "county": "county",
                },
                {
                    "line": ["456 Elm St", "Apt 2"],
                    "city": "Somecity",
                    "state": "CA",
                    "postal_code": "98765-4321",
                    "country": "US",
                    "county": "county2",
                },
            ],
            "telecom": [{"value": "555-123-4567"}, {"value": "555-987-6543"}],
            "drivers_license": {"authority": "VA", "value": "D1234567"},
        }
        record = pii.PIIRecord.model_construct(**data)
        assert record.mrn == "99"
        assert record.birth_date == "1980-2-1"
        assert record.name[0].family == "Doe"
        assert record.name[0].given == ["John", "L"]
        assert record.name[1].family == "Smith"
        assert record.name[1].given == ["Jane"]
        assert record.address[0].line == ["123 Main St"]
        assert record.address[0].city == "Anytown"
        assert record.address[0].state == "NY"
        assert record.address[0].postal_code == "12345"
        assert record.address[0].county == "county"
        assert record.address[1].line == ["456 Elm St", "Apt 2"]
        assert record.address[1].city == "Somecity"
        assert record.address[1].state == "CA"
        assert record.address[1].postal_code == "98765-4321"
        assert record.address[1].county == "county2"
        assert record.drivers_license.value == "D1234567"
        assert record.drivers_license.authority == "VA"

    def test_parse_external_id(self):
        record = pii.PIIRecord(external_id=uuid.UUID("7ca699d9-1986-4c0c-a0fd-ac4ae0dfa297"))
        assert record.external_id == "7ca699d9-1986-4c0c-a0fd-ac4ae0dfa297"
        record = pii.PIIRecord(external_id=12345)
        assert record.external_id == "12345"
        record = pii.PIIRecord(external_id="12345")
        assert record.external_id == "12345"
        record = pii.PIIRecord()
        assert record.external_id is None

    def test_parse_birthdate(self):
        record = pii.PIIRecord(birthDate="1980-01-01")
        assert record.birth_date == datetime.date(1980, 1, 1)
        record = pii.PIIRecord(birthDate="January 1, 1980")
        assert record.birth_date == datetime.date(1980, 1, 1)
        record = pii.PIIRecord(birth_date="Jan 1 1980")
        assert record.birth_date == datetime.date(1980, 1, 1)
        record = pii.PIIRecord(birth_date="1/1/1980")
        assert record.birth_date == datetime.date(1980, 1, 1)
        record = pii.PIIRecord()
        assert record.birth_date is None

    def test_parse_invalid_birthdate(self):
        with pytest.raises(pydantic.ValidationError):
            pii.PIIRecord(birth_date="1 de enero de 1980")

    def test_parse_sex(self):
        record = pii.PIIRecord(sex="M")
        assert record.sex == pii.Sex.MALE
        record = pii.PIIRecord(sex="m")
        assert record.sex == pii.Sex.MALE
        record = pii.PIIRecord(sex="Male")
        assert record.sex == pii.Sex.MALE
        record = pii.PIIRecord(sex="F")
        assert record.sex == pii.Sex.FEMALE
        record = pii.PIIRecord(sex="f")
        assert record.sex == pii.Sex.FEMALE
        record = pii.PIIRecord(sex="FEMALE")
        assert record.sex == pii.Sex.FEMALE
        record = pii.PIIRecord(sex="U")
        assert record.sex == pii.Sex.UNKNOWN
        record = pii.PIIRecord(sex="Unknown")
        assert record.sex == pii.Sex.UNKNOWN
        record = pii.PIIRecord()
        assert record.sex is None

    def test_parse_ssn(self):
        record = pii.PIIRecord(ssn="123-45-6789")
        assert record.ssn == "123-45-6789"
        record = pii.PIIRecord(ssn=" 123-45-6789 ")
        assert record.ssn == "123-45-6789"
        record = pii.PIIRecord(ssn="1-2-3")
        assert record.ssn is None
        record = pii.PIIRecord()
        assert record.ssn is None

    def test_parse_race(self):
        # testing verbose races
        record = pii.PIIRecord(race="american indian or alaska native")
        assert record.race == pii.Race.AMERICAN_INDIAN
        record = pii.PIIRecord(race="black or african american")
        assert record.race == pii.Race.BLACK
        record = pii.PIIRecord(race="native hawaiian or other pacific islander")
        assert record.race == pii.Race.HAWAIIAN
        record = pii.PIIRecord(race="asked but unknown")
        assert record.race == pii.Race.ASKED_UNKNOWN
        record = pii.PIIRecord(race="unknown")
        assert record.race == pii.Race.UNKNOWN

        # testing less verbose races
        record = pii.PIIRecord(race="Asian")
        assert record.race == pii.Race.ASIAN
        record = pii.PIIRecord(race="Black")
        assert record.race == pii.Race.BLACK
        record = pii.PIIRecord(race="Hispanic")
        assert record.race == pii.Race.OTHER
        record = pii.PIIRecord(race="White")
        assert record.race == pii.Race.WHITE
        record = pii.PIIRecord(race="Other")
        assert record.race == pii.Race.OTHER
        record = pii.PIIRecord(race="Hawaiian")
        assert record.race == pii.Race.HAWAIIAN
        record = pii.PIIRecord(race="Pacific Islander")
        assert record.race == pii.Race.HAWAIIAN
        record = pii.PIIRecord(race="African American")
        assert record.race == pii.Race.BLACK
        record = pii.PIIRecord(race="American Indian")
        assert record.race == pii.Race.AMERICAN_INDIAN

        # testing other race
        record = pii.PIIRecord(race="American")
        assert record.race is pii.Race.OTHER

        # testing none result
        record = pii.PIIRecord()
        assert record.race is None

    def test_parse_gender(self):
        # testing verbose genders
        record = pii.PIIRecord(gender="identifies as female gender (finding)")
        assert record.gender == pii.Gender.FEMALE
        record = pii.PIIRecord(gender="identifies as male gender (finding)")
        assert record.gender == pii.Gender.MALE
        record = pii.PIIRecord(gender="identifies as gender nonbinary")
        assert record.gender == pii.Gender.NON_BINARY
        record = pii.PIIRecord(gender="asked but declined")
        assert record.gender == pii.Gender.ASKED_DECLINED
        record = pii.PIIRecord(gender="unknown")
        assert record.gender == pii.Gender.UNKNOWN

        # testing less verbose genders
        record = pii.PIIRecord(gender="Female")
        assert record.gender == pii.Gender.FEMALE
        record = pii.PIIRecord(gender="identifies female")
        assert record.gender == pii.Gender.FEMALE
        record = pii.PIIRecord(gender="Male")
        assert record.gender == pii.Gender.MALE
        record = pii.PIIRecord(gender="identifies male")
        assert record.gender == pii.Gender.MALE
        record = pii.PIIRecord(gender="nonbinary")
        assert record.gender == pii.Gender.NON_BINARY
        record = pii.PIIRecord(gender="declined")
        assert record.gender == pii.Gender.ASKED_DECLINED

        # testing capitalization and leading/trailing spaces
        record = pii.PIIRecord(gender=" Unknown ")
        assert record.gender == pii.Gender.UNKNOWN

        # testing none result
        record = pii.PIIRecord(gender="invalid gender")
        assert record.gender is pii.Gender.UNKNOWN

        record = pii.PIIRecord()
        assert record.gender is None

    def test_feature_iter(self):
        record = pii.PIIRecord(
            external_id="99",
            birth_date="1980-2-1",
            sex="male",
            mrn="123456",
            ssn="123-45-6789",
            race="unknown",
            gender="unknown",
            address=[
                pii.Address(
                    line=["123 Main St"],
                    city="Anytown",
                    state="NY",
                    postalCode="12345",
                    country="US",
                    county="county",
                ),
                pii.Address(
                    line=["456 Elm St", "Apt 2"],
                    city="Somecity",
                    state="CA",
                    postal_code="98765-4321",
                    country="US",
                ),
            ],
            name=[
                pii.Name(family="Doe", given=["John", "L"], suffix=["suffix"]),
                pii.Name(family="Smith", given=["Jane"], suffix=["suffix2"]),
            ],
            telecom=[
                pii.Telecom(value="555-123-4567"),
                pii.Telecom(value="555-987-6543"),
            ],
            drivers_license=pii.DriversLicense(value="D1234567", authority="VA"),
        )

        with pytest.raises(ValueError):
            list(record.feature_iter("external_id"))

        assert list(record.feature_iter(pii.Feature.BIRTHDATE)) == ["1980-02-01"]
        assert list(record.feature_iter(pii.Feature.MRN)) == ["123456"]
        assert list(record.feature_iter(pii.Feature.SEX)) == ["M"]
        assert list(record.feature_iter(pii.Feature.ADDRESS)) == ["123 Main St", "456 Elm St"]
        assert list(record.feature_iter(pii.Feature.CITY)) == ["Anytown", "Somecity"]
        assert list(record.feature_iter(pii.Feature.STATE)) == ["NY", "CA"]
        assert list(record.feature_iter(pii.Feature.ZIP)) == ["12345", "98765"]
        assert list(record.feature_iter(pii.Feature.FIRST_NAME)) == ["John", "L", "Jane"]
        assert list(record.feature_iter(pii.Feature.LAST_NAME)) == ["Doe", "Smith"]
        assert list(record.feature_iter(pii.Feature.SSN)) == ["123-45-6789"]
        assert list(record.feature_iter(pii.Feature.RACE)) == ["UNKNOWN"]
        assert list(record.feature_iter(pii.Feature.GENDER)) == ["UNKNOWN"]
        assert list(record.feature_iter(pii.Feature.TELEPHONE)) == ["555-123-4567", "555-987-6543"]
        assert list(record.feature_iter(pii.Feature.SUFFIX)) == ["suffix", "suffix2"]
        assert list(record.feature_iter(pii.Feature.COUNTY)) == ["county"]
        assert list(record.feature_iter(pii.Feature.DRIVERS_LICENSE)) == ["D1234567|VA"]

    def test_blocking_keys_invalid(self):
        rec = pii.PIIRecord()
        with pytest.raises(ValueError):
            rec.blocking_keys("birthdate")

    @unittest.mock.patch("recordlinker.models.BLOCKING_VALUE_MAX_LENGTH", 1)
    def test_blocking_keys_value_too_long(self):
        rec = pii.PIIRecord(**{"mrn": "123456789"})
        with pytest.raises(RuntimeError):
            rec.blocking_keys(BlockingKey.MRN)

    def test_blocking_keys_birthdate(self):
        rec = pii.PIIRecord(**{"dob": "01/01/1980"})
        assert rec.blocking_keys(BlockingKey.BIRTHDATE) == set()
        rec = pii.PIIRecord(**{"birth_date": "1980-01-01"})
        assert rec.blocking_keys(BlockingKey.BIRTHDATE) == {"1980-01-01"}
        rec = pii.PIIRecord(**{"birthdate": datetime.date(1980, 1, 1)})
        assert rec.blocking_keys(BlockingKey.BIRTHDATE) == {"1980-01-01"}
        rec = pii.PIIRecord(**{"birthDate": "01/01/1980"})
        assert rec.blocking_keys(BlockingKey.BIRTHDATE) == {"1980-01-01"}
        rec = pii.PIIRecord(**{"birthDate": ""})
        assert rec.blocking_keys(BlockingKey.BIRTHDATE) == set()

    def test_blocking_keys_mrn_last_four(self):
        rec = pii.PIIRecord(**{"ssn": "123456789"})
        assert rec.blocking_keys(BlockingKey.MRN) == set()
        rec = pii.PIIRecord(**{"mrn": None})
        assert rec.blocking_keys(BlockingKey.MRN) == set()
        rec = pii.PIIRecord(**{"mrn": "123456789"})
        assert rec.blocking_keys(BlockingKey.MRN) == {"6789"}
        rec = pii.PIIRecord(**{"mrn": "89"})
        assert rec.blocking_keys(BlockingKey.MRN) == {"89"}

    def test_blocking_keys_sex(self):
        rec = pii.PIIRecord(**{"gender": "M"})
        assert rec.blocking_keys(BlockingKey.SEX) == set()
        rec = pii.PIIRecord(**{"sex": ""})
        assert rec.blocking_keys(BlockingKey.SEX) == set()
        rec = pii.PIIRecord(**{"sex": "M"})
        assert rec.blocking_keys(BlockingKey.SEX) == {"M"}
        rec = pii.PIIRecord(**{"sex": "Male"})
        assert rec.blocking_keys(BlockingKey.SEX) == {"M"}
        rec = pii.PIIRecord(**{"sex": "f"})
        assert rec.blocking_keys(BlockingKey.SEX) == {"F"}
        rec = pii.PIIRecord(**{"sex": "FEMALE"})
        assert rec.blocking_keys(BlockingKey.SEX) == {"F"}
        rec = pii.PIIRecord(**{"sex": "other"})
        assert rec.blocking_keys(BlockingKey.SEX) == {"U"}
        rec = pii.PIIRecord(**{"sex": "unknown"})
        assert rec.blocking_keys(BlockingKey.SEX) == {"U"}
        rec = pii.PIIRecord(**{"sex": "?"})
        assert rec.blocking_keys(BlockingKey.SEX) == {"U"}

    def test_blocking_keys_zipcode(self):
        rec = pii.PIIRecord(**{"zip_code": "12345"})
        assert rec.blocking_keys(BlockingKey.ZIP) == set()
        rec = pii.PIIRecord(**{"address": [{"postalCode": None}]})
        assert rec.blocking_keys(BlockingKey.ZIP) == set()
        rec = pii.PIIRecord(**{"address": [{"zipcode": "12345"}]})
        assert rec.blocking_keys(BlockingKey.ZIP) == {"12345"}
        rec = pii.PIIRecord(**{"address": [{"postal_code": "12345-6789"}]})
        assert rec.blocking_keys(BlockingKey.ZIP) == {"12345"}
        rec = pii.PIIRecord(**{"address": [{"zipCode": "12345-6789"}, {"zip": "54321"}]})
        assert rec.blocking_keys(BlockingKey.ZIP) == {"12345", "54321"}

    def test_blocking_keys_first_name_first_four(self):
        rec = pii.PIIRecord(**{"first_name": "John"})
        assert rec.blocking_keys(BlockingKey.FIRST_NAME) == set()
        rec = pii.PIIRecord(**{"name": [{"given": [""], "family": "Doe"}]})
        assert rec.blocking_keys(BlockingKey.FIRST_NAME) == set()
        rec = pii.PIIRecord(**{"name": [{"given": ["John", "Jane"], "family": "Doe"}]})
        assert rec.blocking_keys(BlockingKey.FIRST_NAME) == {"John", "Jane"}
        rec = pii.PIIRecord(
            **{
                "name": [
                    {"given": ["Janet", "Johnathon"], "family": "Doe"},
                    {"given": ["Jane"], "family": "Smith"},
                ]
            }
        )
        assert rec.blocking_keys(BlockingKey.FIRST_NAME) == {"Jane", "John"}

    def test_blocking_keys_last_name_first_four(self):
        rec = pii.PIIRecord(**{"last_name": "Doe"})
        assert rec.blocking_keys(BlockingKey.LAST_NAME) == set()
        rec = pii.PIIRecord(**{"name": [{"family": ""}]})
        assert rec.blocking_keys(BlockingKey.LAST_NAME) == set()
        rec = pii.PIIRecord(**{"name": [{"family": "Doe"}]})
        assert rec.blocking_keys(BlockingKey.LAST_NAME) == {"Doe"}
        rec = pii.PIIRecord(**{"name": [{"family": "Smith"}, {"family": "Doe"}]})
        assert rec.blocking_keys(BlockingKey.LAST_NAME) == {"Smit", "Doe"}

    def test_blocking_keys_address_first_four(self):
        rec = pii.PIIRecord(**{"line": "123 Main St"})
        assert rec.blocking_keys(BlockingKey.ADDRESS) == set()
        rec = pii.PIIRecord(**{"address": [{"line": ["123 Main St"]}]})
        assert rec.blocking_keys(BlockingKey.ADDRESS) == {"123 "}
        rec = pii.PIIRecord(**{"address": [{"line": ["123 Main St", "Apt 2"]}]})
        assert rec.blocking_keys(BlockingKey.ADDRESS) == {"123 "}
        rec = pii.PIIRecord(**{"address": [{"line": ["123 Main St"]}, {"line": ["456 Elm St"]}]})
        assert rec.blocking_keys(BlockingKey.ADDRESS) == {"123 ", "456 "}

    def test_blocking_values(self):
        rec = pii.PIIRecord(
            **{
                "mrn": "123456",
                "birth_date": "1980-01-01",
                "name": [{"given": ["John", "William"], "family": "Doe"}],
            }
        )

        for key, val in rec.blocking_values():
            if key == BlockingKey.BIRTHDATE:
                assert val == "1980-01-01"
            elif key == BlockingKey.MRN:
                assert val == "3456"
            elif key == BlockingKey.FIRST_NAME:
                assert val in ("John", "Will")
            elif key == BlockingKey.LAST_NAME:
                assert val == "Doe"
            else:
                raise AssertionError(f"Unexpected key: {key}")

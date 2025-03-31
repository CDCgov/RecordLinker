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
from recordlinker.models import Patient
from recordlinker.schemas import pii


class TestPIIRecord:
    def test_from_patient(self):
        pat = Patient(data={
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
                    "state": "California",
                    "postal_code": "98765-4321",
                    "country": "US",
                    "county": "county2",
                },
            ],
            "telecom": [{"value": " 555-123-4567"}, {"value": "555-987-6543"}],
            "identifiers": [
                {
                    "type": "MR",
                    "value": "99",
                },
                {
                    "type": "DL",
                    "value": "D1234567",
                    "authority": "VA",
                },
            ],
        })
        record = pii.PIIRecord.from_patient(pat)
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
        assert record.address[1].state == "California"
        assert record.address[1].postal_code == "98765-4321"
        assert record.address[1].county == "county2"

        # identifiers
        assert str(record.identifiers[0].type) == "MR"
        assert record.identifiers[0].value == "99"

        assert str(record.identifiers[1].type) == "DL"
        assert record.identifiers[1].value == "D1234567"
        assert record.identifiers[1].authority == "VA"

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
        record = pii.PIIRecord(birthdate="06-06-74")
        assert record.birth_date == datetime.date(1974, 6, 6)
        record = pii.PIIRecord(birthdate="12-19-08")
        assert record.birth_date == datetime.date(2008, 12, 19)

    def test_parse_invalid_birthdate(self):
        with pytest.raises(pydantic.ValidationError):
            pii.PIIRecord(birth_date="1 de enero de 1980")
        with pytest.raises(pydantic.ValidationError):
            pii.PIIRecord(birth_date="01/01/3000")
        with pytest.raises(pydantic.ValidationError):
            pii.PIIRecord(birth_date="07/10/1543")

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
        assert record.sex is None
        record = pii.PIIRecord(sex="Unknown")
        assert record.sex is None
        record = pii.PIIRecord()
        assert record.sex is None

    def test_parse_ssn(self):
        record = pii.PIIRecord(identifiers=[pii.Identifier(type="SS", value="123-45-6789")])
        assert record.identifiers[0].value == "123-45-6789"
        # testing extra spaces
        record = pii.PIIRecord(identifiers=[pii.Identifier(type="SS", value=" 123-45-6789 ")])
        assert record.identifiers[0].value == "123-45-6789"
        # testing no dashes
        record = pii.PIIRecord(identifiers=[pii.Identifier(type="SS", value="123456789")])
        assert record.identifiers[0].value == "123-45-6789"
        record = pii.PIIRecord(identifiers=[pii.Identifier(type="SS", value="1-2-3")])
        assert record.identifiers[0].value == ""
        record = pii.PIIRecord()
        assert record.identifiers == []

    def test_parse_race(self):
        # testing verbose races
        record = pii.PIIRecord(race=["american indian or alaska native"])
        assert record.race == [pii.Race.AMERICAN_INDIAN]
        record = pii.PIIRecord(race=["black or african american", "asian"])
        assert record.race == [pii.Race.BLACK, pii.Race.ASIAN]
        record = pii.PIIRecord(race=["native hawaiian or other pacific islander"])
        assert record.race == [pii.Race.HAWAIIAN]
        record = pii.PIIRecord(race=["asked unknown"])
        assert record.race == [pii.Race.ASKED_UNKNOWN]
        record = pii.PIIRecord(race=["asked but unknown"])
        assert record.race == [pii.Race.ASKED_UNKNOWN]
        record = pii.PIIRecord(race=["unknown"])
        assert record.race == [pii.Race.UNKNOWN]

        # testing less verbose races
        record = pii.PIIRecord(race=["Asian"])
        assert record.race == [pii.Race.ASIAN]
        record = pii.PIIRecord(race=["Black"])
        assert record.race == [pii.Race.BLACK]
        record = pii.PIIRecord(race=["Hispanic"])
        assert record.race == [pii.Race.OTHER]
        record = pii.PIIRecord(race=["White"])
        assert record.race == [pii.Race.WHITE]
        record = pii.PIIRecord(race=["Other"])
        assert record.race == [pii.Race.OTHER]
        record = pii.PIIRecord(race=["Hawaiian"])
        assert record.race == [pii.Race.HAWAIIAN]
        record = pii.PIIRecord(race=["Pacific Islander", "african american"])
        assert record.race == [pii.Race.HAWAIIAN, pii.Race.BLACK]
        record = pii.PIIRecord(race=["African American"])
        assert record.race == [pii.Race.BLACK]
        record = pii.PIIRecord(race=["American Indian"])
        assert record.race == [pii.Race.AMERICAN_INDIAN]

        # testing other race
        record = pii.PIIRecord(race=["American"])
        assert record.race == [pii.Race.OTHER]

        # testing none result
        record = pii.PIIRecord()
        assert record.race == []

    def test_feature_iter(self):
        record = pii.PIIRecord(
            external_id="99",
            birth_date="1980-2-1",
            sex="male",
            race=["unknown"],
            address=[
                pii.Address(
                    line=[" 123 Main St"],
                    city="Anytown",
                    state="NY",
                    postalCode=" 12345",
                    country="US",
                    county="county",
                ),
                pii.Address(
                    line=["456 Elm St", "Apt 2"],
                    city="Somecity",
                    state="California",
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
                pii.Telecom(value="(555) 987-6543", system="phone"),
                pii.Telecom(value=" teSt@email.com", system="email"),
                pii.Telecom(value="555*987*6543"),
                pii.Telecom(value=" teSt@email.com"),
            ],
            identifiers=[
                {
                    "type": "MR",
                    "value": "123456",
                },
                {
                    "type": "SS",
                    "value": "123-45-6789",
                },
                {
                    "type": "DL",
                    "value": "D1234567",
                    "authority": "VA",
                },
            ],
        )

        with pytest.raises(ValueError):
            list(record.feature_iter("external_id"))

        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.BIRTHDATE))) == [
            "1980-02-01"
        ]
        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.SEX))) == ["M"]
        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.ADDRESS))) == [
            "123mainst",
            "456elmst",
        ]
        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.CITY))) == [
            "anytown",
            "somecity",
        ]
        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.STATE))) == [
            "NY",
            "CA",
        ]
        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.ZIP))) == [
            "12345",
            "98765",
        ]
        assert list(
            record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.GIVEN_NAME))
        ) == ["johnl", "jane"]
        assert list(
            record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.FIRST_NAME))
        ) == ["john", "jane"]
        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.LAST_NAME))) == [
            "doe",
            "smith",
        ]
        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.RACE))) == []
        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.TELECOM))) == [
            "555-123-4567",
            "5559876543",
            "test@email.com",
            "555*987*6543",
            "test@email.com",
        ]

        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.PHONE))) == [
            "5559876543"
        ]
        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.EMAIL))) == [
            "test@email.com"
        ]
        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.SUFFIX))) == [
            "suffix",
            "suffix2",
        ]
        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.COUNTY))) == [
            "county"
        ]
        assert list(
            record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.IDENTIFIER))
        ) == ["123456::MR", "123456789::SS", "d1234567:va:DL"]

        # IDENTIFIER with suffix
        assert list(
            record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.IDENTIFIER, suffix="MR"))
        ) == ["123456::MR"]
        assert list(
            record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.IDENTIFIER, suffix="SS"))
        ) == ["123456789::SS"]

        # Other fields work okay, few more checks on difference race yield values
        record = pii.PIIRecord(race=["asked unknown"])
        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.RACE))) == []
        record = pii.PIIRecord(race=["asked but unknown"])
        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.RACE))) == []
        record = pii.PIIRecord(race=["asian"])
        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.RACE))) == [
            "ASIAN"
        ]
        record = pii.PIIRecord(race=["african american"])
        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.RACE))) == [
            "BLACK"
        ]
        record = pii.PIIRecord(race=["white"])
        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.RACE))) == [
            "WHITE"
        ]

    def test_feature_iter_given_name(self):
        record = pii.PIIRecord(
            name=[
                pii.Name(family="Doe", given=["John", "L"], suffix=["suffix"]),
                pii.Name(family="Smith", given=["Jon", "Lewis", "Doe"], suffix=["suffix2"]),
            ],
        )

        assert list(
            record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.GIVEN_NAME))
        ) == ["johnl", "jonlewisdoe"]
        assert list(
            record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.FIRST_NAME))
        ) == ["john", "jon"]

    def test_feature_iter_state(self):
        record = pii.PIIRecord(
            address=[
                pii.Address(state="new york"),
                pii.Address(state="NY"),
                pii.Address(state="California"),
                pii.Address(state=" california "),
                pii.Address(state="of mind"),
            ]
        )

        assert list(record.feature_iter(pii.Feature(attribute=pii.FeatureAttribute.STATE))) == [
            "NY",
            "NY",
            "CA",
            "CA",
            "of mind",
        ]

    def test_blocking_keys_invalid(self):
        rec = pii.PIIRecord()
        with pytest.raises(ValueError):
            rec.blocking_keys("birthdate")

    @unittest.mock.patch("recordlinker.models.BLOCKING_VALUE_MAX_LENGTH", 1)
    def test_blocking_keys_value_too_long(self):
        rec = pii.PIIRecord(**{"identifiers": [{"type": "MR", "value": "123456789"}]})
        with pytest.raises(RuntimeError):
            rec.blocking_keys(BlockingKey.IDENTIFIER)

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
        rec = pii.PIIRecord()
        assert rec.blocking_keys(BlockingKey.IDENTIFIER) == set()
        rec = pii.PIIRecord(**{"identifiers": []})
        assert rec.blocking_keys(BlockingKey.IDENTIFIER) == set()
        rec = pii.PIIRecord(**{"identifiers": [{"type": "MR", "value": "123456789"}]})
        assert rec.blocking_keys(BlockingKey.IDENTIFIER) == {"6789:MR"}
        rec = pii.PIIRecord(**{"identifiers": [{"type": "MR", "value": "89"}]})
        assert rec.blocking_keys(BlockingKey.IDENTIFIER) == {"89:MR"}

        # test multiple identifiers return correctly
        rec = pii.PIIRecord(
            identifiers=[
                pii.Identifier(type="MR", value="123456789"),
                pii.Identifier(type="SS", value="123456789"),
            ]
        )
        assert rec.blocking_keys(BlockingKey.IDENTIFIER) == {"6789:MR", "6789:SS"}

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
        assert rec.blocking_keys(BlockingKey.SEX) == set()
        rec = pii.PIIRecord(**{"sex": "unknown"})
        assert rec.blocking_keys(BlockingKey.SEX) == set()
        rec = pii.PIIRecord(**{"sex": "?"})
        assert rec.blocking_keys(BlockingKey.SEX) == set()

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
        rec = pii.PIIRecord(**{"address": [{"zipCode": " 12345-6789"}, {"zip": " 54321 "}]})
        assert rec.blocking_keys(BlockingKey.ZIP) == {"12345", "54321"}

    def test_blocking_keys_first_name_first_four(self):
        rec = pii.PIIRecord(**{"first_name": "john"})
        assert rec.blocking_keys(BlockingKey.FIRST_NAME) == set()
        rec = pii.PIIRecord(**{"name": [{"given": [""], "family": "doe"}]})
        assert rec.blocking_keys(BlockingKey.FIRST_NAME) == set()
        rec = pii.PIIRecord(**{"name": [{"given": ["john", "jane"], "family": "doe"}]})
        assert rec.blocking_keys(BlockingKey.FIRST_NAME) == {"john"}
        rec = pii.PIIRecord(
            **{
                "name": [
                    {"given": ["Janet", "Johnathon"], "family": "Doe"},
                    {"given": ["Jane"], "family": "Smith"},
                ]
            }
        )
        assert rec.blocking_keys(BlockingKey.FIRST_NAME) == {"jane"}

    def test_blocking_keys_last_name_first_four(self):
        rec = pii.PIIRecord(**{"last_name": "Doe"})
        assert rec.blocking_keys(BlockingKey.LAST_NAME) == set()
        rec = pii.PIIRecord(**{"name": [{"family": ""}]})
        assert rec.blocking_keys(BlockingKey.LAST_NAME) == set()
        rec = pii.PIIRecord(**{"name": [{"family": "Doe"}]})
        assert rec.blocking_keys(BlockingKey.LAST_NAME) == {"doe"}
        rec = pii.PIIRecord(**{"name": [{"family": "Smith"}, {"family": "Doe"}]})
        assert rec.blocking_keys(BlockingKey.LAST_NAME) == {"smit", "doe"}

    def test_blocking_keys_address_first_four(self):
        rec = pii.PIIRecord(**{"line": "123 Main St"})
        assert rec.blocking_keys(BlockingKey.ADDRESS) == set()
        rec = pii.PIIRecord(**{"address": [{"line": ["123 Main St"]}]})
        assert rec.blocking_keys(BlockingKey.ADDRESS) == {"123m"}
        rec = pii.PIIRecord(**{"address": [{"line": ["123 Main St", "Apt 2"]}]})
        assert rec.blocking_keys(BlockingKey.ADDRESS) == {"123m"}
        rec = pii.PIIRecord(**{"address": [{"line": ["123 Main St"]}, {"line": ["456 Elm St"]}]})
        assert rec.blocking_keys(BlockingKey.ADDRESS) == {"123m", "456e"}

    def test_blocking_keys_phone_last_four(self):
        rec = pii.PIIRecord(**{"phone": "555-123-4567"})
        assert rec.blocking_keys(BlockingKey.PHONE) == set()
        rec = pii.PIIRecord(**{"telecom": [{"value": "(555) 123-4567", "system": "phone"}]})
        assert rec.blocking_keys(BlockingKey.PHONE) == {"4567"}
        rec = pii.PIIRecord(
            **{
                "telecom": [
                    {"value": "555.123.4567", "system": "phone"},
                    {"value": "555-987-6543 ext 123", "system": "phone"},
                ]
            }
        )
        assert rec.blocking_keys(BlockingKey.PHONE) == {"4567", "6543"}
        rec = pii.PIIRecord(
            **{
                "telecom": [
                    {"value": "555.123.4567 ", "system": "phone"},
                    {"value": "555-987-6543", "system": "fax"},
                ]
            }
        )
        assert rec.blocking_keys(BlockingKey.PHONE) == {"4567"}

    def test_blocking_keys_email_first_four(self):
        rec = pii.PIIRecord(**{"email": "test123@email.com"})
        assert rec.blocking_keys(BlockingKey.EMAIL) == set()
        rec = pii.PIIRecord(**{"telecom": [{"value": "test123@email.com", "system": "email"}]})
        assert rec.blocking_keys(BlockingKey.EMAIL) == {"test"}
        rec = pii.PIIRecord(
            **{
                "telecom": [
                    {"value": "test@email.com", "system": "email"},
                    {"value": " bob@email.com", "system": "email"},
                ]
            }
        )
        assert rec.blocking_keys(BlockingKey.EMAIL) == {"test", "bob@"}
        rec = pii.PIIRecord(
            **{
                "telecom": [
                    {"value": "t@gmail.com", "system": "email"},
                    {"value": "bob@gmail.com", "system": "other"},
                ]
            }
        )
        assert rec.blocking_keys(BlockingKey.EMAIL) == {"t@gm"}

    def test_blocking_keys_identifier(self):
        rec = pii.PIIRecord(**{"identifiers": []})
        assert rec.blocking_keys(BlockingKey.IDENTIFIER) == set()
        rec = pii.PIIRecord(
            **{"identifiers": [{"type": "MR", "value": "123456789", "authority": "NY"}]}
        )
        assert rec.blocking_keys(BlockingKey.IDENTIFIER) == {"6789:MR"}

        # test only get first 2 characters of authority for blocking
        rec = pii.PIIRecord(
            **{"identifiers": [{"type": "MR", "value": "123456789", "authority": "DMV"}]}
        )
        assert rec.blocking_keys(BlockingKey.IDENTIFIER) == {"6789:MR"}

    def test_blocking_values(self):
        rec = pii.PIIRecord(
            **{
                "identifiers": [{"type": "MR", "value": "3456"}],
                "birth_date": "1980-01-01",
                "name": [{"given": ["John", "William"], "family": "Doe"}],
            }
        )

        for key, val in rec.blocking_values():
            if key == BlockingKey.BIRTHDATE:
                assert val == "1980-01-01"
            elif key == BlockingKey.IDENTIFIER:
                assert val == "3456:MR"
            elif key == BlockingKey.FIRST_NAME:
                assert val == "john"
            elif key == BlockingKey.LAST_NAME:
                assert val == "doe"
            else:
                raise AssertionError(f"Unexpected key: {key}")

class TestAddress:
    def test_parse_line(self):
        address = pii.Address(line=["123 Main St.", "Apt 2"])
        assert address.line[0] == "123 Main ST"
        assert address.line[1] == "Apt 2"

        address = pii.Address(line=["123 Main Jctn", "Suite"])
        assert address.line[0] == "123 Main JCT"
        assert address.line[1] == "Suite"

        address = pii.Address(line=[" 123 Main avenue "])
        assert address.line[0] == "123 Main AVE"

    def test_parse_state(self):
        address = pii.Address(state=" New York") 
        assert address.state == "NY"
        address = pii.Address(state="oregon")
        assert address.state == "OR"
        address = pii.Address(state="wa")
        assert address.state == "WA"
        address = pii.Address(state="district of  columbia")
        assert address.state == "DC"
        address = pii.Address(state=" Armed Forces")
        assert address.state == "Armed Forces"
        address = pii.Address(state="Conneticut")
        assert address.state == "Conneticut"

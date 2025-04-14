"""
unit.linking.test_clean.py
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.linking.clean module.
"""

from recordlinker import schemas
from recordlinker.linking import clean
from recordlinker.schemas.algorithm import SkipValue
from recordlinker.schemas.identifier import IdentifierType
from recordlinker.schemas.pii import Race


class TestMatches:
    def test_no_matches(self):
        assert not clean.matches("foo", ["bar"])
        assert not clean.matches("foo", ["bar", "baz"])
        assert not clean.matches("foo", ["b*"])

    def test_matches(self):
        assert clean.matches("foo", ["foo"])
        assert clean.matches("foo", ["bar", "foo"])
        assert clean.matches("foo", ["f*"])
        assert clean.matches("foo", ["f??"])


class TestClean:
    def test_asterisk(self):
        skips = [SkipValue(feature="*", values=["UNKNOWN"])]
        cleaned = clean.clean(schemas.PIIRecord(name=[{"given": ["John"], "family": "Doe"}]), skips)
        assert cleaned.name[0].given == ["John"]
        assert cleaned.name[0].family == "Doe"
        cleaned = clean.clean(
            schemas.PIIRecord(name=[{"given": ["John"], "family": "UNKNOWN"}]), skips
        )
        assert cleaned.name[0].given == ["John"]
        assert cleaned.name[0].family == ""
        cleaned = clean.clean(
            schemas.PIIRecord(
                name=[{"given": ["UNKNOWN", "L"], "family": "Doe"}], address=[{"zip": "UNKNOWN"}]
            ),
            skips,
        )
        assert cleaned.name[0].given == ["", "L"]
        assert cleaned.name[0].family == "Doe"
        assert cleaned.address[0].postal_code == ""
        cleaned = clean.clean(schemas.PIIRecord(race=["UNKNOWN"]), skips)
        assert cleaned.race == [None]

    def test_case_insensitive(self):
        skips = [SkipValue(feature="*", values=["austin"])]
        cleaned = clean.clean(
            schemas.PIIRecord(name=[{"given": ["Austin"], "family": "Doe"}]), skips
        )
        assert cleaned.name[0].given == [""]
        assert cleaned.name[0].family == "Doe"
        cleaned = clean.clean(schemas.PIIRecord(address=[{"city": "AUSTIN"}]), skips)
        assert cleaned.address[0].city == ""

    def test_birthdate(self):
        skips = [SkipValue(feature="BIRTHDATE", values=["2000-01-01"])]
        cleaned = clean.clean(schemas.PIIRecord(birth_date="2000-01-01"), skips)
        assert cleaned.birth_date is None

    def test_sex(self):
        skips = [SkipValue(feature="SEX", values=["M"])]
        cleaned = clean.clean(schemas.PIIRecord(sex="M"), skips)
        assert cleaned.sex is None

    def test_address(self):
        skips = [SkipValue(feature="ADDRESS", values=["123 Fake *"])]
        cleaned = clean.clean(
            schemas.PIIRecord(address=[{"line": ["123 Fake St"]}, {"line": ["53 Fake Ave"]}]), skips
        )
        assert cleaned.address[0].line[0] == ""
        assert cleaned.address[1].line[0] == "53 Fake AVE"

    def test_city(self):
        skips = [SkipValue(feature="CITY", values=["CITY"])]
        cleaned = clean.clean(schemas.PIIRecord(address=[{"city": "city"}]), skips)
        assert cleaned.address[0].city == ""

    def test_state(self):
        skips = [SkipValue(feature="STATE", values=["AA"])]
        cleaned = clean.clean(schemas.PIIRecord(address=[{"state": "aa"}]), skips)
        assert cleaned.address[0].state == ""

    def test_zip(self):
        skips = [SkipValue(feature="ZIP", values=["00000*"])]
        cleaned = clean.clean(schemas.PIIRecord(address=[{"postal_code": "00000"}]), skips)
        assert cleaned.address[0].postal_code == ""
        cleaned = clean.clean(schemas.PIIRecord(address=[{"postal_code": "00000-1111"}]), skips)
        assert cleaned.address[0].postal_code == ""

    def test_county(self):
        skips = [SkipValue(feature="COUNTY", values=["missing"])]
        cleaned = clean.clean(schemas.PIIRecord(address=[{"county": "MISSING"}]), skips)
        assert cleaned.address[0].county == ""

    def test_given_name(self):
        skips = [SkipValue(feature="GIVEN_NAME", values=["fake"])]
        cleaned = clean.clean(
            schemas.PIIRecord(name=[{"given": ["fake", "jane"], "family": "Doe"}]), skips
        )
        assert cleaned.name[0].given == ["", "jane"]
        assert cleaned.name[0].family == "Doe"

    def test_first_name(self):
        skips = [SkipValue(feature="FIRST_NAME", values=["fake"])]
        cleaned = clean.clean(
            schemas.PIIRecord(name=[{"given": ["fake", "fake"], "family": "Doe"}]), skips
        )
        assert cleaned.name[0].given == ["", "fake"]
        assert cleaned.name[0].family == "Doe"

    def test_last_name(self):
        skips = [SkipValue(feature="LAST_NAME", values=["fake"])]
        cleaned = clean.clean(
            schemas.PIIRecord(name=[{"given": ["john", "jane"], "family": "fake"}]), skips
        )
        assert cleaned.name[0].given == ["john", "jane"]
        assert cleaned.name[0].family == ""

    def test_suffix(self):
        skips = [SkipValue(feature="SUFFIX", values=["UNK"])]
        cleaned = clean.clean(
            schemas.PIIRecord(name=[{"family": "fake", "suffix": ["unk"]}]), skips
        )
        assert cleaned.name[0].family == "fake"
        assert cleaned.name[0].suffix == [""]

    def test_race(self):
        skips = [SkipValue(feature="RACE", values=["UNKNOWN"])]
        cleaned = clean.clean(schemas.PIIRecord(race=["UNKNOWN", "WHITE"]), skips)
        assert cleaned.race == [None, Race.WHITE]

    def test_telecom(self):
        skips = [SkipValue(feature="TELECOM", values=["+15555555555"])]
        cleaned = clean.clean(
            schemas.PIIRecord(telecom=[{"system": "phone", "value": "555-555-5555"}]), skips
        )
        assert cleaned.telecom[0].system == "phone"
        assert cleaned.telecom[0].value == ""

    def test_phone(self):
        skips = [SkipValue(feature="PHONE", values=["+15555555555"])]
        cleaned = clean.clean(
            schemas.PIIRecord(
                telecom=[
                    {"system": "phone", "value": "555-555-5555"},
                    {"system": "fax", "value": "+15555555555"},
                ]
            ),
            skips,
        )
        assert cleaned.telecom[0].system == "phone"
        assert cleaned.telecom[0].value == ""
        assert cleaned.telecom[1].system == "fax"
        assert cleaned.telecom[1].value == "+15555555555"

    def test_email(self):
        skips = [SkipValue(feature="EMAIL", values=["fake@*.com"])]
        cleaned = clean.clean(
            schemas.PIIRecord(telecom=[{"system": "email", "value": "fake@aol.com"}]), skips
        )
        assert cleaned.telecom[0].system == "email"
        assert cleaned.telecom[0].value == ""
        cleaned = clean.clean(
            schemas.PIIRecord(telecom=[{"system": "email", "value": "fake@earthlink.net"}]), skips
        )
        assert cleaned.telecom[0].system == "email"
        assert cleaned.telecom[0].value == "fake@earthlink.net"

    def test_identifier(self):
        skips = [SkipValue(feature="IDENTIFIER", values=["fake:*"])]
        cleaned = clean.clean(
            schemas.PIIRecord(identifiers=[{"type": "DL", "value": "fake"}]), skips
        )
        assert cleaned.identifiers[0].type == IdentifierType.DL
        assert cleaned.identifiers[0].value == ""
        skips = [SkipValue(feature="IDENTIFIER:MR", values=["999999999:*"])]
        cleaned = clean.clean(
            schemas.PIIRecord(identifiers=[{"type": "DL", "value": "999999999"}]), skips
        )
        assert cleaned.identifiers[0].type == IdentifierType.DL
        assert cleaned.identifiers[0].value == "999999999"
        cleaned = clean.clean(
            schemas.PIIRecord(identifiers=[{"type": "MR", "value": "999999999"}]), skips
        )
        assert cleaned.identifiers[0].type == IdentifierType.MR
        assert cleaned.identifiers[0].value == ""
        skips = [SkipValue(feature="IDENTIFIER", values=["99-999-9999::SS"])]
        cleaned = clean.clean(
            schemas.PIIRecord(identifiers=[{"type": "SS", "value": "99-999-9999"}]), skips
        )
        assert cleaned.identifiers[0].type == IdentifierType.SS
        assert cleaned.identifiers[0].value == ""
        cleaned = clean.clean(
            schemas.PIIRecord(identifiers=[{"type": "MR", "value": "99-999-9999"}]), skips
        )
        assert cleaned.identifiers[0].type == IdentifierType.MR
        assert cleaned.identifiers[0].value == "99-999-9999"

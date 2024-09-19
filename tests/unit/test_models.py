"""
unit.test_models.py
~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.linkage.models module.
"""

import datetime

from recordlinker.linkage import models


class TestBlockingKey:
    def test_extract_birthdate(self):
        data = {"dob": "01/01/1980"}
        assert models.BlockingKey.BIRTHDATE.to_value(data) == set()
        data = {"birthdate": "01/01/1980"}
        assert models.BlockingKey.BIRTHDATE.to_value(data) == {"1980-01-01"}
        data = {"birthdate": datetime.date(1980, 1, 1)}
        assert models.BlockingKey.BIRTHDATE.to_value(data) == {"1980-01-01"}
        data = {"birthdate": datetime.datetime(1980, 1, 1, 12, 30, 0)}
        assert models.BlockingKey.BIRTHDATE.to_value(data) == {"1980-01-01"}

    def test_extract_mrn_last_four(self):
        data = {"ssn": "123456789"}
        assert models.BlockingKey.MRN.to_value(data) == set()
        data = {"mrn": "123456789"}
        assert models.BlockingKey.MRN.to_value(data) == {"6789"}
        data = {"mrn": "89"}
        assert models.BlockingKey.MRN.to_value(data) == {"89"}

    def test_extract_sex(self):
        data = {"gender": "M"}
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
        data = {"zip": "12345"}
        assert models.BlockingKey.ZIP.to_value(data) == set()
        data = {"address": [{"zip": "12345"}]}
        assert models.BlockingKey.ZIP.to_value(data) == {"12345"}
        data = {"address": [{"zip": "12345-6789"}]}
        assert models.BlockingKey.ZIP.to_value(data) == {"12345"}
        data = {"address": [{"zip": "12345-6789"}, {"zip": "54321"}]}
        assert models.BlockingKey.ZIP.to_value(data) == {"12345", "54321"}

    def test_extract_first_name_first_four(self):
        data = {"first_name": "John"}
        assert models.BlockingKey.FIRST_NAME.to_value(data) == set()
        data = {"name": [{"given": ["John", "Jane"]}]}
        assert models.BlockingKey.FIRST_NAME.to_value(data) == {"John", "Jane"}
        data = {"name": [{"given": ["Janet", "Johnathon"]}, {"given": ["Jane"]}]}
        assert models.BlockingKey.FIRST_NAME.to_value(data) == {"Jane", "John"}

    def test_extract_last_name_first_four(self):
        data = {"last_name": "Doe"}
        assert models.BlockingKey.LAST_NAME.to_value(data) == set()
        data = {"name": [{"family": "Doe"}]}
        assert models.BlockingKey.LAST_NAME.to_value(data) == {"Doe"}
        data = {"name": [{"family": "Smith"}, {"family": "Doe"}]}
        assert models.BlockingKey.LAST_NAME.to_value(data) == {"Smit", "Doe"}

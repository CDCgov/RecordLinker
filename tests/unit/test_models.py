"""
unit.test_models.py
~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.linkage.models module.
"""

import datetime
import unittest

from recordlinker.linkage import models


class BlockingKeyTests(unittest.TestCase):
    def test_extract_birthdate(self):
        data = {"dob": "01/01/1980"}
        self.assertEqual(
            models.BlockingKey.BIRTHDATE.to_value(data), []
        )
        data = {"birthdate": "01/01/1980"}
        self.assertEqual(
            models.BlockingKey.BIRTHDATE.to_value(data), ["1980-01-01"]
        )
        data = {"birthdate": datetime.date(1980, 1, 1)}
        self.assertEqual(
            models.BlockingKey.BIRTHDATE.to_value(data), ["1980-01-01"]
        )
        data = {"birthdate": datetime.datetime(1980, 1, 1, 12, 30, 0)}
        self.assertEqual(
            models.BlockingKey.BIRTHDATE.to_value(data), ["1980-01-01"]
        )

    def test_extract_mrn_last_four(self):
        data = {"ssn": "123456789"}
        self.assertEqual(models.BlockingKey.MRN.to_value(data), [])
        data = {"mrn": "123456789"}
        self.assertEqual(models.BlockingKey.MRN.to_value(data), ["6789"])
        data = {"mrn": "89"}
        self.assertEqual(models.BlockingKey.MRN.to_value(data), ["89"])

    def test_extract_sex(self):
        data = {"gender": "M"}
        self.assertEqual(models.BlockingKey.SEX.to_value(data), [])
        data = {"sex": "M"}
        self.assertEqual(models.BlockingKey.SEX.to_value(data), ["m"])
        data = {"sex": "Male"}
        self.assertEqual(models.BlockingKey.SEX.to_value(data), ["m"])
        data = {"sex": "f"}
        self.assertEqual(models.BlockingKey.SEX.to_value(data), ["f"])
        data = {"sex": "FEMALE"}
        self.assertEqual(models.BlockingKey.SEX.to_value(data), ["f"])
        data = {"sex": "other"}
        self.assertEqual(models.BlockingKey.SEX.to_value(data), ["u"])
        data = {"sex": "unknown"}
        self.assertEqual(models.BlockingKey.SEX.to_value(data), ["u"])
        data = {"sex": "?"}
        self.assertEqual(models.BlockingKey.SEX.to_value(data), ["u"])

    def test_extract_zipcode(self):
        data = {"zip": "12345"}
        self.assertEqual(models.BlockingKey.ZIP.to_value(data), [])
        data = {"address": [{"zip": "12345"}]}
        self.assertEqual(models.BlockingKey.ZIP.to_value(data), ["12345"])
        data = {"address": [{"zip": "12345-6789"}]}
        self.assertEqual(models.BlockingKey.ZIP.to_value(data), ["12345"])
        data = {"address": [{"zip": "12345-6789"}, {"zip": "54321"}]}
        self.assertEqual(models.BlockingKey.ZIP.to_value(data), ["12345", "54321"])

    def test_extract_first_name_first_four(self):
        data = {"first_name": "John"}
        self.assertEqual(models.BlockingKey.FIRST_NAME.to_value(data), [])
        data = {"name": [{"given": ["John", "Jane"]}]}
        self.assertEqual(
            models.BlockingKey.FIRST_NAME.to_value(data), ["John", "Jane"]
        )
        data = {"name": [{"given": ["Janet", "Johnathon"]}]}
        self.assertEqual(
            models.BlockingKey.FIRST_NAME.to_value(data), ["Jane", "John"]
        )

    def test_extract_last_name_first_four(self):
        data = {"last_name": "Doe"}
        self.assertEqual(models.BlockingKey.LAST_NAME.to_value(data), [])
        data = {"name": [{"family": "Doe"}]}
        self.assertEqual(models.BlockingKey.LAST_NAME.to_value(data), ["Doe"])
        data = {"name": [{"family": "Smith"}, {"family": "Doe"}]}
        self.assertEqual(models.BlockingKey.LAST_NAME.to_value(data), ["Smit", "Doe"])

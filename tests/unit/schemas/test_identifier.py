"""
unit.schemas.test_identifier.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.schemas.identifier module.
"""
import pytest

from recordlinker.schemas import identifier


class TestIdentifier:
    def test_model_construct(self):
        obj = identifier.Identifier.model_construct(type="MR", value="123456789", authority="NY")
        assert obj.type == identifier.IdentifierType.MR
        assert obj.value == "123456789"
        assert obj.authority == "NY"

        with pytest.raises(ValueError):
            identifier.Identifier.model_construct(type="X", value="123456789", authority="NY")

    def test_normalize_ssn_value(self):
        with pytest.raises(ValueError):
            identifier.Identifier(type=None, value="123-45-67890")

        obj = identifier.Identifier(type="SS", value="123-45-6789")
        assert obj.type == identifier.IdentifierType.SS
        assert obj.value == "123-45-6789"
        assert obj.authority is None

        obj = identifier.Identifier(type="SS", value=" 123456789")
        assert obj.type == identifier.IdentifierType.SS
        assert obj.value == "123-45-6789"
        assert obj.authority is None

        obj = identifier.Identifier(type="MR", value="123456789")
        assert obj.type == identifier.IdentifierType.MR
        assert obj.value == "123456789"
        assert obj.authority is None

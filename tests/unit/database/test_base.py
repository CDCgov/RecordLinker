"""
unit.database.test_base.py
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.database module.
"""
import os
import unittest.mock

from recordlinker.config import settings
from recordlinker.database import create_sessionmaker
from recordlinker.database import tables


def test_tables():
    """
    Test the tables function.
    """
    with unittest.mock.patch.dict("os.environ", {"TUNING_ENABLED": "true"}):
        settings.__init__()
        assert len(tables()) == 5
    with unittest.mock.patch.dict("os.environ", {"TUNING_ENABLED": "false"}):
        settings.__init__()
        assert len(tables()) == 4


def test_create_sessionmaker():
    """
    Test the create_sessionmaker function.
    """
    with unittest.mock.patch.dict(
        "os.environ",
        {
            "DB_URI": "sqlite:///test.db",
            "CONNECTION_POOL_SIZE": "10",
            "CONNECTION_POOL_MAX_OVERFLOW": "20",
        },
    ):
        settings.__init__()
        session = create_sessionmaker()()
        assert str(session.bind.url) == "sqlite:///test.db"
        assert session.bind.pool.size() == 10
        assert session.bind.pool._max_overflow == 20
    settings.__init__()
    try:
        os.remove("test.db")
    except FileNotFoundError:
        pass

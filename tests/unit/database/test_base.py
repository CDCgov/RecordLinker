"""
unit.database.test_base.py
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.database module.
"""
import os
import unittest.mock

import pytest
from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text

from recordlinker import models
from recordlinker.config import settings
from recordlinker.database import create_sessionmaker
from recordlinker.database import verify_tables_match_orm


@pytest.fixture
def in_memory_engine():
    """
    Fixture for an in-memory SQLite engine.
    """
    engine = create_engine("sqlite:///:memory:")
    models.Base.metadata.create_all(engine)  # Create tables as defined by ORM
    return engine

class TableForTesting(models.Base):
    __tablename__ = "test_table"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)

# def test_create_sessionmaker():
#     """
#     Test the create_sessionmaker function.
#     """
#     with unittest.mock.patch.dict(
#         "os.environ",
#         {
#             "DB_URI": "sqlite:///test.db",
#             "CONNECTION_POOL_SIZE": "10",
#             "CONNECTION_POOL_MAX_OVERFLOW": "20",
#         },
#     ):
#         settings.__init__()
#         session = create_sessionmaker()()
#         assert str(session.bind.url) == "sqlite:///test.db"
#         assert session.bind.pool.size() == 10
#         assert session.bind.pool._max_overflow == 20
#     settings.__init__()
#     try:
#         os.remove("test.db")
#     except FileNotFoundError:
#         pass

def test_verify_tables_match_orm_no_mismatch(in_memory_engine):
    """
    Test that verify_tables_match_orm passes when the database schema matches the ORM.
    """
    models.Base.metadata.create_all(in_memory_engine)  # Create tables as defined by ORM

    try:
        verify_tables_match_orm(in_memory_engine)
    except SQLAlchemyError:
        pytest.fail("verify_tables_match_orm raised an exception with a matching schema.")

# def test_verify_tables_match_orm_missing_column(in_memory_engine):
#     """
#     Test that verify_tables_match_orm raises an error when a column is missing.
#     """
#     # Drop a column from the database schema
#     with in_memory_engine.connect() as connection:
#         connection.execute(text("ALTER TABLE test_table DROP COLUMN age"))

#     with pytest.raises(SQLAlchemyError, match="Column 'age' is missing in the database for table 'test_table'"):
#         verify_tables_match_orm(in_memory_engine)

# def test_verify_tables_match_orm_missing_table(in_memory_engine):
#     """
#     Test that verify_tables_match_orm raises an error when a table is missing.
#     """
#     # Drop the table from the database
#     with in_memory_engine.connect() as connection:
#         connection.execute(text("DROP TABLE test_table"))

#     with pytest.raises(SQLAlchemyError, match="Table 'test_table' is missing in the database."):
#         verify_tables_match_orm(in_memory_engine)

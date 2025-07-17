"""
unit.database.test_base.py
~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.database module.
"""

import tempfile
import unittest.mock

import pytest
from alembic import command as alembic_command
from alembic import config as alembic_config
from sqlalchemy import inspect
from sqlalchemy.engine import create_engine
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.sql import func

from recordlinker import models
from recordlinker.config import settings
from recordlinker.database import create_sessionmaker
from recordlinker.database import get_random_function
from recordlinker.database import tables
from recordlinker.utils.path import rel_path
from recordlinker.utils.path import repo_root


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


class TestCreateSessionmaker:
    def existing_tables(self, uri) -> set[str]:
        engine = create_engine(uri)
        return set(inspect(engine).get_table_names())

    def existing_rl_tables(self, uri) -> set[str]:
        rl_tables: set[str] = {str(t) for t in tables()}
        return self.existing_tables(uri) & rl_tables

    def stamp_migrations(self):
        repo = repo_root()
        assert repo is not None
        alembic_cfg = alembic_config.Config(toml_file=rel_path(repo / "pyproject.toml"))
        alembic_command.stamp(alembic_cfg, "head")

    def test_init_databse(self):
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".db", delete=True) as tmp:
            db_uri = f"sqlite:///{tmp.name}"
            with unittest.mock.patch.dict(
                "os.environ",
                {
                    "DB_URI": db_uri,
                    "CONNECTION_POOL_SIZE": "10",
                    "CONNECTION_POOL_MAX_OVERFLOW": "20",
                    "TUNING_ENABLED": "true",
                },
            ):
                settings.__init__()
                assert len(self.existing_rl_tables(db_uri)) == 0
                assert "alembic_version" not in self.existing_tables(db_uri)
                session = create_sessionmaker(auto_migrate=True)()
                assert len(self.existing_rl_tables(db_uri)) == 5
                assert "alembic_version" in self.existing_tables(db_uri)
                assert str(session.bind.url) == db_uri
                assert session.bind.pool.size() == 10
                assert session.bind.pool._max_overflow == 20
            settings.__init__()

    def test_init_migrations(self):
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".db", delete=True) as tmp:
            db_uri = f"sqlite:///{tmp.name}"
            with unittest.mock.patch.dict(
                "os.environ",
                {
                    "DB_URI": db_uri,
                    "CONNECTION_POOL_SIZE": "10",
                    "CONNECTION_POOL_MAX_OVERFLOW": "20",
                    "TUNING_ENABLED": "true",
                },
            ):
                settings.__init__()
                models.Base.metadata.create_all(create_engine(db_uri))
                assert "alembic_version" not in self.existing_tables(db_uri)
                assert len(self.existing_rl_tables(db_uri)) == 5
                session = create_sessionmaker(auto_migrate=True)()
                assert len(self.existing_rl_tables(db_uri)) == 5
                assert "alembic_version" in self.existing_tables(db_uri)
                assert str(session.bind.url) == db_uri
                assert session.bind.pool.size() == 10
                assert session.bind.pool._max_overflow == 20
            settings.__init__()

    def test_upgrade_migrations(self):
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".db", delete=True) as tmp:
            db_uri = f"sqlite:///{tmp.name}"
            with unittest.mock.patch.dict(
                "os.environ",
                {
                    "DB_URI": db_uri,
                    "CONNECTION_POOL_SIZE": "10",
                    "CONNECTION_POOL_MAX_OVERFLOW": "20",
                    "TUNING_ENABLED": "true",
                },
            ):
                settings.__init__()
                models.Base.metadata.create_all(create_engine(db_uri))
                self.stamp_migrations()
                assert "alembic_version" in self.existing_tables(db_uri)
                assert len(self.existing_rl_tables(db_uri)) == 5
                session = create_sessionmaker(auto_migrate=True)()
                assert len(self.existing_rl_tables(db_uri)) == 5
                assert "alembic_version" in self.existing_tables(db_uri)
                assert str(session.bind.url) == db_uri
                assert session.bind.pool.size() == 10
                assert session.bind.pool._max_overflow == 20
            settings.__init__()


class TestGetRandomFunction:
    class FakeDialect(Dialect):
        "Fake dialect class for testing."

        def __init__(self, name):
            self.name = name

    @pytest.mark.parametrize(
        "dialect_name,expected_func",
        [
            ("sqlite", func.random),
            ("postgresql", func.random),
            ("mysql", func.rand),
            ("mssql", func.newid),
        ],
    )
    def test_known_dialects(self, dialect_name, expected_func):
        dialect = self.FakeDialect(dialect_name)
        result = get_random_function(dialect)
        assert str(result).startswith(str(expected_func())), f"Failed for dialect: {dialect_name}"

    def test_unsupported_dialect(self):
        dialect = self.FakeDialect("oracle")
        with pytest.raises(NotImplementedError, match="Unsupported DB dialect: oracle"):
            get_random_function(dialect)

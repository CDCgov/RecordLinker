"""
recordlinker.database
~~~~~~~~~~~~~~~~~~~~~

This module contains the database connection and session management functions.
"""

import contextlib
import typing

from alembic import command as alembic_command
from alembic import config as alembic_config
from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy import orm
from sqlalchemy import schema

from recordlinker import models
from recordlinker.config import settings


def tables() -> list[schema.Table]:
    """
    Get a list of all tables in the database.
    """
    tables = list(models.Base.metadata.tables.values())
    if not settings.tuning_enabled:
        return [t for t in tables if not t.name.startswith("tuning_")]
    return tables


def create_sessionmaker(init_tables: bool = True) -> orm.sessionmaker:
    """
    Create a new sessionmaker for the database connection.
    """
    kwargs: dict[str, typing.Any] = {}
    if settings.connection_pool_size is not None:
        kwargs["pool_size"] = settings.connection_pool_size
    if settings.connection_pool_max_overflow is not None:
        kwargs["max_overflow"] = settings.connection_pool_max_overflow
    engine = create_engine(settings.db_uri, **kwargs)
    if init_tables:
        is_empty_db: bool = inspect(engine).get_table_names() == []
        if is_empty_db:
            # When the database is empty, create all the tables and mark
            # the alembic migrations as applied
            models.Base.metadata.create_all(engine, tables=tables())
            alembic_cfg = alembic_config.Config(toml_file="pyproject.toml")
            alembic_command.stamp(alembic_cfg, "head")
    return orm.sessionmaker(bind=engine)


def get_session() -> typing.Iterator[orm.Session]:
    """
    Get a new session from the sessionmaker.
    """
    with SessionMaker() as session:
        try:
            yield session
            session.commit()
        except Exception as exc:
            session.rollback()
            raise exc
        finally:
            session.close()


@contextlib.contextmanager
def get_test_session() -> typing.Iterator[orm.Session]:
    """
    Get a new session from the sessionmaker for testing.
    """
    engine = create_engine(settings.test_db_uri)
    # Create all the tables
    models.Base.metadata.create_all(engine, tables=tables())
    session = orm.scoped_session(orm.sessionmaker(bind=engine))()
    try:
        yield session
    finally:
        # Tear down the session and drop the schema
        session.close()
        models.Base.metadata.drop_all(engine, tables=tables())


SessionMaker = create_sessionmaker(init_tables=settings.initialize_tables)
get_session_manager = contextlib.contextmanager(get_session)

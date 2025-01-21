"""
recordlinker.database
~~~~~~~~~~~~~~~~~~~~~

This module contains the database connection and session management functions.
"""

import contextlib
import typing

from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy import orm
from sqlalchemy.exc import SQLAlchemyError

from recordlinker import models
from recordlinker.config import settings


def create_sessionmaker(init_tables: bool = True, verify_tables: bool = True) -> orm.sessionmaker:
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
        models.Base.metadata.create_all(engine)
    if verify_tables:
        verify_tables_match_orm(engine)

    return orm.sessionmaker(bind=engine)

def are_types_equivalent(db_type, orm_type) -> bool:
    # Using a str wrapper to normalize types from different contexts (inspector types vs ORM types)
    db_type_str = str(db_type).lower()
    orm_type_str = str(orm_type).lower()

    # Treat these cases as equivalent
    if {db_type_str, orm_type_str} <= {"integer", "bigint"}:
        return True
    
    if {db_type_str, orm_type_str} <= {"double precision", "float"}:
        return True

    return db_type_str == orm_type_str

def verify_tables_match_orm(engine):
    """
    Verify that database tables match ORM definitions.
    """
    inspector = inspect(engine)
    orm_metadata = models.Base.metadata

    for table_name, orm_table in orm_metadata.tables.items():
        if not inspector.has_table(table_name):
            raise SQLAlchemyError(
                f"Table '{table_name}' is missing in the database."
            )

        db_columns = inspector.get_columns(table_name)
        db_column_details = {col['name']: col for col in db_columns}

        for orm_column in orm_table.columns:
            column_name = orm_column.name

            if column_name not in db_column_details:
                raise SQLAlchemyError(
                    f"Column '{column_name}' is missing in the database for table '{table_name}'."
                )

            db_col_type = db_column_details[column_name]['type']
            orm_col_type = orm_column.type

            if not are_types_equivalent(db_col_type, orm_col_type):
                raise SQLAlchemyError(
                    f"Type mismatch for column '{column_name}' in table '{table_name}': "
                    f"DB type is {db_col_type}, ORM type is {orm_col_type}."
                )

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
    models.Base.metadata.create_all(engine)
    session = orm.scoped_session(orm.sessionmaker(bind=engine))()
    try:
        yield session
    finally:
        # Tear down the session and drop the schema
        session.close()
        models.Base.metadata.drop_all(engine)


SessionMaker = create_sessionmaker()

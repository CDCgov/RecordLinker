"""
recordlinker.database
~~~~~~~~~~~~~~~~~~~~~

This module contains the database connection and session management functions.
"""

import typing

from sqlalchemy import create_engine
from sqlalchemy import orm

from recordlinker import models
from recordlinker.config import settings


def create_sessionmaker(init_tables: bool = True) -> orm.sessionmaker:
    """
    Create a new sessionmaker for the database connection.
    """
    engine = create_engine(
        settings.db_uri,
        pool_size=settings.connection_pool_size,
        max_overflow=settings.connection_pool_max_overflow,
    )
    if init_tables:
        models.Base.metadata.create_all(engine)
    return orm.sessionmaker(autocommit=False, bind=engine)


Session = create_sessionmaker()


def get_session() -> typing.Iterator[orm.Session]:
    """
    Get a new session from the sessionmaker.
    """
    with Session() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

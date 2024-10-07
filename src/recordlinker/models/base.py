from sqlalchemy import create_engine
from sqlalchemy import orm
from sqlalchemy import types as sqltypes

from recordlinker.config import settings


class Base(orm.DeclarativeBase):
    pass


def get_session() -> orm.Session:
    """
    Creates a new session to the MPI database and returns it.
    """
    engine = create_engine(
        url=settings.db_uri,
        pool_size=settings.connection_pool_size,
        max_overflow=settings.connection_pool_max_overflow,
    )
    Base.metadata.create_all(engine)
    return orm.Session(engine)



def get_bigint_pk():
    """
    Most databases support auto-incrementing primary keys using BIGINT, however SQLite
    does not support it.  Thus for the SQLite dialect, we need to use INTEGER instead.
    """
    return sqltypes.BigInteger().with_variant(sqltypes.INTEGER, "sqlite")

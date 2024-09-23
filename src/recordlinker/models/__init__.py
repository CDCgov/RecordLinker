from sqlalchemy import create_engine
from sqlalchemy import orm

from recordlinker.config import settings


def get_session() -> orm.Session:
    """
    Creates a new session to the MPI database and returns it.
    """
    engine = create_engine(settings.db_uri)
    Base.metadata.create_all(engine)
    return orm.Session(engine)


class Base(orm.DeclarativeBase):
    pass

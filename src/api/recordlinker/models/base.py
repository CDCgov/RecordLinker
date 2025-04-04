from sqlalchemy import orm
from sqlalchemy import types as sqltypes

from recordlinker.config import settings


class PrefixerMeta(orm.DeclarativeMeta):

    def __init__(cls, name, bases, dict_):
        name = dict_.get("__tablename__")
        if name:
            cls.__tablename__ = f"{settings.db_table_prefix}{name}"
            dict_["__tablename__"] = f"{settings.db_table_prefix}{name}"
        return super().__init__(name, bases, dict_)

Base = orm.declarative_base(metaclass=PrefixerMeta)


def get_bigint_pk():
    """
    Most databases support auto-incrementing primary keys using BIGINT, however SQLite
    does not support it.  Thus for the SQLite dialect, we need to use INTEGER instead.
    """
    return sqltypes.BigInteger().with_variant(sqltypes.INTEGER, "sqlite")

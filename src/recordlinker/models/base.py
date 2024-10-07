from sqlalchemy import orm
from sqlalchemy import types as sqltypes


class Base(orm.DeclarativeBase):
    pass


def get_bigint_pk():
    """
    Most databases support auto-incrementing primary keys using BIGINT, however SQLite
    does not support it.  Thus for the SQLite dialect, we need to use INTEGER instead.
    """
    return sqltypes.BigInteger().with_variant(sqltypes.INTEGER, "sqlite")


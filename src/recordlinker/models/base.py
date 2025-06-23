import datetime

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


class TZDateTime(sqltypes.TypeDecorator):
    """
    Custom DateTime type that ensures timezone-awareness (defaults to UTC).
    Works like sqlalchemy.DateTime(timezone=False), but always returns tz-aware values.
    """

    impl = sqltypes.DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """
        Convert aware datetime to naive before storing if timezone=False
        """
        if value is not None and value.tzinfo is not None:
            return value.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        """
        Ensure tz-aware datetime (assuming stored in UTC)
        """
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=datetime.timezone.utc)
        return value

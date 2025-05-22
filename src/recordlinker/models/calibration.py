import datetime
import enum
import uuid

from sqlalchemy import orm
from sqlalchemy import types as sqltypes

from .base import Base


class Status(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"


class Job(Base):
    __tablename__ = "calibration_job"
    id: orm.Mapped[uuid.UUID] = orm.mapped_column(
        sqltypes.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    status: orm.Mapped[Status] = orm.mapped_column(
        sqltypes.Enum(Status, name="status_enum", native_enum=False),
        default=Status.PENDING,
        nullable=False
    )
    created_at = orm.mapped_column(
        sqltypes.DateTime,
        default=datetime.datetime.utcnow,
        nullable=False,
    )
    updated_at = orm.mapped_column(
        sqltypes.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

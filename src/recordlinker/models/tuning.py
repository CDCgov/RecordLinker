import enum
import uuid

from sqlalchemy import orm
from sqlalchemy import types as sqltypes

from recordlinker.utils.datetime import now_utc

from .base import Base


class TuningStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TuningJob(Base):
    __tablename__ = "tuning_job"
    id: orm.Mapped[uuid.UUID] = orm.mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    status: orm.Mapped[TuningStatus] = orm.mapped_column(
        sqltypes.Enum(TuningStatus, name="status_enum", native_enum=False),
        nullable=False,
    )
    params: orm.Mapped[dict] = orm.mapped_column(sqltypes.JSON, default=dict)
    results: orm.Mapped[dict] = orm.mapped_column(sqltypes.JSON, default=dict)
    started_at = orm.mapped_column(
        sqltypes.DateTime,
        default=now_utc,
        nullable=False,
    )
    finished_at = orm.mapped_column(
        sqltypes.DateTime,
        default=None,
        nullable=True,
    )

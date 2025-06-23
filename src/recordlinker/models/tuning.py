import datetime
import enum
import uuid

from sqlalchemy import orm
from sqlalchemy import types as sqltypes

from recordlinker.utils.datetime import now_utc_no_ms

from .base import Base
from .base import TZDateTime


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
    params: orm.Mapped[dict] = orm.mapped_column(sqltypes.JSON, nullable=False)
    results: orm.Mapped[dict] = orm.mapped_column(sqltypes.JSON, default=None, nullable=True)
    started_at = orm.mapped_column(
        TZDateTime,
        default=now_utc_no_ms(),
        nullable=False,
    )
    finished_at = orm.mapped_column(
        TZDateTime,
        default=None,
        nullable=True,
    )

    @property
    def duration(self) -> datetime.timedelta:
        """
        Get the duration of the tuning job.
        """
        last_ts: datetime.datetime = self.finished_at or now_utc_no_ms()
        return last_ts - self.started_at

"""
recordlinker.database.tuning_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides the data access functions to the tuning_job table
"""

import logging
import typing
import uuid

from sqlalchemy import engine
from sqlalchemy import orm
from sqlalchemy import sql

from recordlinker.config import settings
from recordlinker.models import tuning as models
from recordlinker.schemas import tuning as schemas
from recordlinker.utils.datetime import now_utc_no_ms

LOGGER = logging.getLogger(__name__)


def start_job(
    session: orm.Session, params: schemas.TuningParams, commit: bool = True
) -> schemas.TuningJob:
    """
    Start a new tuning job.
    """
    job = schemas.TuningJob(params=params)
    session.add(models.TuningJob(**job.model_dump()))
    if commit:
        session.commit()
    return job


def get_job(session: orm.Session, job_id: uuid.UUID) -> typing.Optional[schemas.TuningJob]:
    """
    Get a tuning job by its ID
    """
    obj = session.get(models.TuningJob, job_id)
    if obj is None:
        return None
    return schemas.TuningJob.model_validate(obj)


def update_job(
    session: orm.Session,
    job: schemas.TuningJob,
    status: models.TuningStatus,
    results: typing.Optional[schemas.TuningResults] = None,
    commit: bool = True,
) -> schemas.TuningJob:
    """
    Update a tuning job.
    """
    job.status = status
    if status in (models.TuningStatus.COMPLETED, models.TuningStatus.FAILED):
        job.finished_at = now_utc_no_ms()
    if results is not None:
        job.results = results

    # build a dict of model fields and their values, excluding id
    data: dict[str, typing.Any] = job.model_dump(
        include=(set(models.TuningJob.__table__.columns.keys()) - {"id"})
    )
    result: engine.CursorResult = session.execute(
        sql.update(models.TuningJob).where(models.TuningJob.id == job.id).values(**data)
    )
    if result.rowcount == 0:
        raise ValueError(f"Failed to update job {job.id}")
    if commit:
        session.commit()
    return job


def fail_job(session: orm.Session, job_id: uuid.UUID, message: str) -> None:
    """
    Mark a tuning job as timed out.
    """
    results = schemas.TuningResults(details=message)
    stmt = (
        sql.update(models.TuningJob)
        .where(models.TuningJob.id == job_id)
        .values(
            status=models.TuningStatus.FAILED,
            results=results.model_dump(),
            finished_at=now_utc_no_ms(),
        )
    )
    session.execute(stmt)
    session.commit()


def get_active_jobs(session: orm.Session) -> typing.Sequence[schemas.TuningJob]:
    """
    Get all TuningJobs that are active.  If a job is still listed as active, and
    has timed out, it will be canceled.
    """
    jobs: list[schemas.TuningJob] = []
    query = (
        session.query(models.TuningJob)
        .filter(
            models.TuningJob.status.in_([models.TuningStatus.PENDING, models.TuningStatus.RUNNING])
        )
        .all()
    )
    # check to see if any jobs have timed out and need to be canceled
    for obj in query:
        job = schemas.TuningJob.model_validate(obj)
        if obj.duration.total_seconds() > settings.tuning_job_timeout:
            LOGGER.warning(
                "tuning job canceled", extra={"job_id": job.id, "age": obj.duration.total_seconds()}
            )
            fail_job(session, job.id, "canceled incomplete job")
            continue
        jobs.append(job)
    return jobs

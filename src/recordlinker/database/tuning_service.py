"""
recordlinker.linking.tuning_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides the data access functions to the tuning_job table
"""

import typing
import uuid

from sqlalchemy import orm

from recordlinker.models import tuning as models
from recordlinker.schemas import tuning as schemas
from recordlinker.utils.datetime import now_utc


def start_job(session: orm.Session, params: schemas.TuningParams, commit: bool = True) -> schemas.TuningJob:
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
    job = session.get(models.TuningJob, job_id)
    if job is None:
        return None
    return schemas.TuningJob.model_validate(job)


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
        job.finished_at = now_utc()
    if results is not None:
        job.results = results

    obj = session.get(models.TuningJob, job.id)
    if obj is None:
        raise ValueError("Job not found")
    for field, value in job.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    if commit:
        session.commit()
    return job

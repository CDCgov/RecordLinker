"""
recordlinker.routes.calibration_router
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the calibration router for the RecordLinker API. Exposing
the API endpoints to initiate and manage a calibration job.
"""

import time
import uuid

import fastapi
import pydantic
import sqlalchemy.orm as orm

from recordlinker import models
from recordlinker.database import get_session
from recordlinker.database import SessionMaker

router = fastapi.APIRouter()


class CalibrationBody(pydantic.BaseModel):
    delay: int = pydantic.Field(..., gt=0, description="Delay in seconds.")


class CalibrationJob(pydantic.BaseModel):
    id: uuid.UUID = pydantic.Field(..., description="The identifier for the calibration job.")
    status: models.Status = pydantic.Field(..., description="The status of the calibration job.")


class JobService:
    def __init__(self, session):
        self.session = session

    def create_job(self) -> models.Job:
        ""
        job = models.Job()
        self.session.add(job)
        self.session.flush()
        return job

    def get_job(self, id: uuid.UUID) -> models.Job:
        ""
        return self.session.get(models.Job, id)

    def complete_job(self, id: uuid.UUID) -> models.Job:
        ""
        job = self.get_job(id)
        job.status = models.Status.COMPLETED
        self.session.flush()
        return job


def test_job(id: uuid.UUID, delay: int):
    ""
    time.sleep(delay)
    db = SessionMaker()
    try:
        service = JobService(db)
        service.complete_job(id)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.post("/test", status_code=fastapi.status.HTTP_202_ACCEPTED, name="start-test")
def start_test(
    session: orm.Session = fastapi.Depends(get_session),
    data: CalibrationBody = fastapi.Body(...),
    background_tasks: fastapi.BackgroundTasks = fastapi.BackgroundTasks(),
) -> CalibrationJob:
    """
    Start a new calibration job in the MPI database.

    :param data: The calibration job data
    :returns: The created calibration job
    """
    service = JobService(session)
    job = service.create_job()
    background_tasks.add_task(test_job, job.id, data.delay)
    return CalibrationJob(id=job.id, status=job.status)


@router.get("/test/{id}", status_code=fastapi.status.HTTP_200_OK, name="get-test")
def get_test(id: uuid.UUID, session: orm.Session = fastapi.Depends(get_session)) -> CalibrationJob:
    """
    Get an existing calibration job from the MPI database.

    :param id: The calibration job identifier
    :returns: The calibration job
    """
    service = JobService(session)
    job = service.get_job(id)
    if job is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)
    return CalibrationJob(id=job.id, status=job.status)

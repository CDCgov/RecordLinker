"""
recordlinker.routes.tuning_router
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the tuning router for the RecordLinker API. Exposing
endpoints to manage tuning jobs.
"""

import asyncio
import logging
import uuid

import fastapi
import sqlalchemy.orm as orm

from recordlinker import schemas
from recordlinker.config import settings
from recordlinker.database import get_session
from recordlinker.database import get_session_manager
from recordlinker.database import tuning_service as service
from recordlinker.tuning import tune

LOGGER = logging.getLogger(__name__)

router = fastapi.APIRouter()


async def run_tune_job(job_id: uuid.UUID):
    """
    Run log-odds tuning calculations, with a timeout to prevent long-running jobs.
    """
    timeout: int = settings.tuning_job_timeout
    try:
        await asyncio.wait_for(tune(job_id), timeout=timeout)
    except Exception as exc:
        # Tuning job either failed on its own, or ran out of time.
        # In either case, we're going to log the error, mark the job
        # as failed in the database and exit the background task
        msg: str= "job timed out" if isinstance(exc, asyncio.TimeoutError) else str(exc)
        LOGGER.error(msg, extra={"job_id": job_id, "timeout": timeout})
        with get_session_manager() as session:
            service.fail_job(session, job_id, msg)


@router.post(
    "",
    summary="Create tuning job",
    status_code=fastapi.status.HTTP_202_ACCEPTED,
    name="create-tuning-job",
)
def create(
    request: fastapi.Request,
    session: orm.Session = fastapi.Depends(get_session),
    background_tasks: fastapi.BackgroundTasks = fastapi.BackgroundTasks(),
) -> schemas.TuningJobResponse:
    """
    Create a new tuning job.
    """
    if service.get_active_jobs(session):
        # Don't allow more than one tuning job to run at a time
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_409_CONFLICT,
            detail="Tuning job already in progress",
        )
    params = schemas.TuningParams(
        true_match_pairs=settings.tuning_true_match_pairs,
        non_match_pairs=settings.tuning_non_match_pairs,
    )
    # Commit the job early, so the data is available in the database for the
    # background task before the response is returned
    job = service.start_job(session, params, commit=True)
    background_tasks.add_task(run_tune_job, job.id)
    LOGGER.info("tuning job started", extra={"job_id": job.id})
    return schemas.TuningJobResponse.from_tuning_job(job, request)


@router.get(
    "/{job_id}",
    summary="Get tuning job",
    status_code=fastapi.status.HTTP_200_OK,
    name="get-tuning-job",
)
def get(
    request: fastapi.Request,
    job_id: uuid.UUID,
    session: orm.Session = fastapi.Depends(get_session),
) -> schemas.TuningJobResponse:
    """
    Get a tuning job by its ID.
    """
    job = service.get_job(session, job_id)
    if job is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)
    return schemas.TuningJobResponse.from_tuning_job(job, request)

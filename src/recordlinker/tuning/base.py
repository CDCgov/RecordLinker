"""
recordlinker.tuning.base
~~~~~~~~~~~~~~~~~~~~~~~~

This module provides functions for running log-odds tuning calculations
"""

import logging
import typing
import uuid

from recordlinker import models
from recordlinker.database import get_session_manager
from recordlinker.database import tuning_service

LOGGER = logging.getLogger(__name__)


async def tune(job_id: uuid.UUID, session_factory: typing.Optional[typing.Callable] = None) -> None:
    """
    Run log-odds tuning calculations
    """
    LOGGER.info("tuning job received", extra={"job_id": job_id})
    session_factory = session_factory or get_session_manager
    with session_factory() as session:
        job = tuning_service.get_job(session, job_id)
        if job is None:
            LOGGER.error("tuning job not found", extra={"job_id": job_id})
            raise ValueError(f"Tuning job not found: {job_id}")
        try:
            tuning_service.update_job(session, job, models.TuningStatus.RUNNING)
            # TODO: get true and non-match pairs
            # TODO: calculate m- and u-probabilities
            # TODO: calculate log-odds
            # TODO: calculate pass recommendations
            # TODO: update results and set job
        except Exception as exc:
            LOGGER.error("tuning job failed", extra={"job_id": job_id, "exc": str(exc)})
            tuning_service.fail_job(session, job_id, str(exc))
            raise

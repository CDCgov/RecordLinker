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
        tuning_service.update_job(session, job, models.TuningStatus.RUNNING)
        # TODO: run log-odds tuning

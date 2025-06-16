"""
recordlinker.tuning.base
~~~~~~~~~~~~~~~~~~~~~~~~

This module provides functions for running log-odds tuning calculations
"""
import uuid

from recordlinker import models
from recordlinker.database import SessionMaker
from recordlinker.database import tuning_service


def tune(job_id: uuid.UUID) -> None:
    """
    Run log-odds tuning calculations
    """
    session = SessionMaker()
    job = tuning_service.get_job(session, job_id)
    if job is None:
        raise ValueError(f"Tuning job not found: {job_id}")
    tuning_service.update_job(session, job, models.TuningStatus.RUNNING)
    # TODO: run log-odds tuning

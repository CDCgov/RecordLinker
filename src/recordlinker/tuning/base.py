"""
recordlinker.tuning.base
~~~~~~~~~~~~~~~~~~~~~~~~

This module provides functions for running log-odds tuning calculations
"""

import logging
import typing
import uuid

from recordlinker import models
from recordlinker import schemas
from recordlinker.database import get_session_manager
from recordlinker.database import mpi_service
from recordlinker.database import tuning_service

from . import prob_calc

LOGGER = logging.getLogger(__name__)


# TODO: test cases
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
            results: schemas.TuningResults = schemas.TuningResults()

            # # CALCULATE M-PROBABILITIES
            # true_pairs: typing.Sequence[typing.Tuple[dict, dict]] = (
                # mpi_service.generate_true_match_tuning_samples(
                    # session,
                    # job.params.true_match_pairs_requested,
                # )
            # )
            # results.true_match_pairs_used = len(true_pairs)
            # m_probs: dict[str, float] = prob_calc.calculate_class_probs(true_pairs)
            # del true_pairs

            # # CALCULATE U-PROBABILITIES
            # non_pairs: typing.Sequence[typing.Tuple[dict, dict]] = (
                # mpi_service.generate_non_match_tuning_samples(
                    # session,
                    # sample_size=job.params.non_match_sample_requested,
                    # n_pairs=job.params.non_match_pairs_requested,
                # )
            # )
            # results.non_match_pairs_used = len(non_pairs)
            # # TODO: set non_match_sample_used
            # u_probs: dict[str, float] = prob_calc.calculate_class_probs(non_pairs)
            # del non_pairs

            # log_odds: dict[str, float] = prob_calc.calculate_log_odds(
                # m_probs=m_probs, u_probs=u_probs
            # )
            # results.log_odds = [
                # schemas.LogOdd(feature=schemas.Feature.parse(k), value=v) for k, v in log_odds.items()
            # ]
            # # TODO: calculate pass recommendations
            tuning_service.update_job(session, job, models.TuningStatus.COMPLETED, results)
        except Exception as exc:
            LOGGER.error("tuning job failed", extra={"job_id": job_id, "exc": str(exc)})
            tuning_service.fail_job(session, job_id, str(exc))

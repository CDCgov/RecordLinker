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
from recordlinker.database.algorithm_service import default_algorithm
from recordlinker.tuning import prob_calc

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

            # Step 1: Acquire class-partitioned data samples and update
            # results information with number of pairs actually used
            true_pairs: typing.Sequence[typing.Tuple[dict, dict]] = (
                mpi_service.generate_true_match_tuning_samples(
                    session,
                    job.params.true_match_pairs_requested,
                )
            )
            non_pairs, sample_used = mpi_service.generate_non_match_tuning_samples(
                session,
                sample_size=job.params.non_match_sample_requested,
                n_pairs=job.params.non_match_pairs_requested,
            )
            results.true_match_pairs_used = len(true_pairs)
            results.non_match_pairs_used = len(non_pairs)
            results.non_match_sample_used = sample_used

            # Step 2: Compute class-specific probabilities
            m_probs: dict[str, float] = prob_calc.calculate_class_probs(true_pairs)
            u_probs: dict[str, float] = prob_calc.calculate_class_probs(non_pairs)

            # Step 3: Compute log-odds
            log_odds: dict[str, float] = prob_calc.calculate_log_odds(
                m_probs=m_probs, u_probs=u_probs
            )
            results.log_odds = [
                schemas.LogOdd(
                    feature=schemas.Feature.parse(k), value=v
                ) for k, v in log_odds.items()
            ]

            # Step 4: Compute suggested RMS possible match window boundaries
            algorithm = default_algorithm(session)
            assert algorithm is not None
            sorted_scores: dict[str, typing.Tuple[list[float], list[float]]] = (
                prob_calc.calculate_and_sort_tuning_scores(
                    true_pairs, non_pairs, log_odds, algorithm
                )
            )
            rms_bounds: dict[str, typing.Tuple[float, float]] = (
                prob_calc.estimate_rms_bounds(sorted_scores)
            )
            pass_recs: list[schemas.tuning.PassRecommendation] = []
            pass_list: list[
                typing.Tuple[int, schemas.AlgorithmPass]
            ] = enumerate(algorithm.passes)
            for idx, algorithm_pass in pass_list:
                pass_name: str = algorithm_pass.label or f"pass_{idx}"
                rec = schemas.tuning.PassRecommendation(
                    pass_label=pass_name,
                    recommended_match_window=rms_bounds[pass_name]
                )
                pass_recs.append(rec)
            results.passes = pass_recs

            tuning_service.update_job(session, job, models.TuningStatus.COMPLETED, results)
        except Exception as exc:
            LOGGER.error("tuning job failed", extra={"job_id": job_id, "exc": str(exc)})
            tuning_service.fail_job(session, job_id, str(exc))

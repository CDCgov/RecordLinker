"""
recordlinker.tuning.base
~~~~~~~~~~~~~~~~~~~~~~~~

This module provides functions for running log-odds tuning calculations
"""

import logging
import typing
import uuid

from sqlalchemy import orm

from recordlinker import models
from recordlinker import schemas
from recordlinker.database import get_session_manager
from recordlinker.database import mpi_service
from recordlinker.database import tuning_service
from recordlinker.database.algorithm_service import default_algorithm
from recordlinker.tuning import prob_calc

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
            results: schemas.TuningResults = schemas.TuningResults()

            (true_count, non_count, non_sample, log_odds) = run_log_odds(session, job.params)
            results.true_match_pairs_used = true_count
            results.non_match_pairs_used = non_count
            results.non_match_sample_used = non_sample
            results.passes = run_rms(session, job.params, results.log_odds)

            tuning_service.update_job(session, job, models.TuningStatus.COMPLETED, results)
        except Exception as exc:
            LOGGER.error(
                "tuning job failed", extra={"job_id": job_id, "exc": str(exc)}, exc_info=True
            )
            tuning_service.fail_job(session, job_id, str(exc))


def run_log_odds(
    session: orm.Session, params: schemas.TuningParams
) -> typing.Tuple[int, int, int, typing.Sequence[schemas.LogOdd]]:
    """
    Run log-odds tuning calculations

    :param session: database session
    :param params: tuning parameters

    :returns: A tuple of the form (true_match_count, non_match_count,
      sample_used, log_odds)
    """
    # Step 1: Acquire class-partitioned data samples and update
    # results information with number of pairs actually used
    true_pairs: typing.Iterator[prob_calc.TuningPair] = (
        mpi_service.generate_true_match_tuning_samples(
            session,
            params.true_match_pairs_requested,
        )
    )
    non_pairs: typing.Iterator[prob_calc.TuningPair] = (
        mpi_service.generate_non_match_tuning_samples(
            session,
            sample_size=params.non_match_sample_requested,
            n_pairs=params.non_match_pairs_requested,
        )
    )

    # Step 2: Compute class-specific probabilities
    m_results: schemas.TuningProbabilities = prob_calc.calculate_class_probs(true_pairs)
    u_results: schemas.TuningProbabilities = prob_calc.calculate_class_probs(non_pairs)

    # Step 3: Compute log-odds
    log_odds: dict[schemas.Feature, float] = prob_calc.calculate_log_odds(
        m_probs=m_results.probs, u_probs=u_results.probs
    )

    return (
        m_results.count,
        u_results.count,
        u_results.sample_used or 0,
        [schemas.LogOdd(feature=f, value=v) for f, v in log_odds.items()],
    )


def run_rms(
    session: orm.Session, params: schemas.TuningParams, log_odds: typing.Sequence[schemas.LogOdd]
) -> typing.Sequence[schemas.PassRecommendation]:
    """
    Run RMS tuning calculations

    :param session: database session
    :param params: tuning parameters
    :param log_odds: log-odds values

    :returns: A sequence of PassRecommendation
    """
    obj: models.Algorithm | None = default_algorithm(session)
    if obj is None:
        # No default Algorithm found, so no RMS tuning can be performed
        return []

    algorithm: schemas.Algorithm = schemas.Algorithm.model_validate(obj)
    log_odds_map: dict[schemas.Feature, float] = {f.feature: f.value for f in log_odds}

    # Step 1: Acquire class-partitioned data samples and update
    # results information with number of pairs actually used
    true_pairs: typing.Iterator[prob_calc.TuningPair] = (
        mpi_service.generate_true_match_tuning_samples(
            session,
            params.true_match_pairs_requested,
        )
    )
    non_pairs: typing.Iterator[prob_calc.TuningPair] = (
        mpi_service.generate_non_match_tuning_samples(
            session,
            sample_size=params.non_match_sample_requested,
            n_pairs=params.non_match_pairs_requested,
        )
    )

    # Step 2: Compute suggested RMS possible match window boundaries
    sorted_scores: dict[str, typing.Tuple[list[float], list[float]]] = (
        prob_calc.calculate_and_sort_tuning_scores(true_pairs, non_pairs, log_odds_map, algorithm)
    )
    rms_bounds: dict[str, typing.Tuple[float, float]] = prob_calc.estimate_rms_bounds(sorted_scores)
    pass_recs: list[schemas.PassRecommendation] = []
    for idx, algorithm_pass in enumerate(algorithm.passes):
        pass_name: str = algorithm_pass.resolved_label
        rec = schemas.PassRecommendation(
            algorithm_label=algorithm.label,
            pass_label=pass_name,
            recommended_match_window=rms_bounds[pass_name],
        )
        pass_recs.append(rec)
    return pass_recs

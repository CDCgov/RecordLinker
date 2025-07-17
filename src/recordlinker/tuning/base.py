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
def tune(job_id: uuid.UUID, session_factory: typing.Optional[typing.Callable] = None) -> None:
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
        
        # Some early fail-fasts if the user hasn't requested enough data to
        # make tuning results meaningful
        if job.params.true_match_pairs_requested < 1000:
            LOGGER.error("too few true match pairs requested", extra={
                "job_id": job_id, "true_match_pairs_requested": job.params.true_match_pairs_requested
            })
            raise ValueError(f"Too few true match pairs requested for job {job_id}: minimum permitted 1000, {job.params.true_match_pairs_requested} requested")
        if job.params.non_match_sample_requested < 10000:
            LOGGER.error("too few non match samples requested", extra={
                "job_id": job_id, "non_match_samples_requested": job.params.non_match_sample_requested
            })
            raise ValueError(f"Too few non match samples requested for job {job_id}: minimum permitted 10000, {job.params.non_match_sample_requested} requested")

        if job.params.non_match_pairs_requested < 1000:
            LOGGER.error("too few non match pairs requested", extra={
                "job_id": job_id, "non_match_pairs_requested": job.params.non_match_pairs_requested
            })
            raise ValueError(f"Too few non match pairs requested for job {job_id}: minimum permitted 1000, {job.params.non_match_pairs_requested} requested")

        try:
            # Pre-flight checks: DB must be non-empty, have more than one Person 
            # cluster, and not have a single monolith Person in order to tune
            db_empty: bool = mpi_service.check_mpi_non_empty(session)
            if db_empty:
                LOGGER.error("no patient data in MPI", extra={"job_id": job_id})
                raise ValueError("MPI contains no patient data")
            acceptable_structure, unique_person_ids = mpi_service.check_mpi_has_acceptable_cluster_structure(session)
            if not acceptable_structure:
                LOGGER.error("MPI Person cluster structure invalid for tuning", extra={"job_id": job_id, "num_person_clusters_in_MPI": unique_person_ids})
                raise ValueError(f"MPI has person structure that does not support tuning: must have num_person_clusters greater than 1 and less than num_patients, have {unique_person_ids}")

            tuning_service.update_job(session, job, models.TuningStatus.RUNNING)
            results: schemas.TuningResults = schemas.TuningResults()

            # Step 1: Acquire class-partitioned data samples and update
            # results information with number of pairs actually used
            true_iter: typing.Iterator[typing.Tuple[dict, dict]] = (
                mpi_service.generate_true_match_tuning_samples(
                    session,
                    job.params.true_match_pairs_requested,
                )
            )
            true_pairs: list[typing.Tuple[dict, dict]] = list(true_iter)
            if len(true_pairs) < 3000:
                LOGGER.warning(
                    "Fewer than recommended true-match pairs found in MPI, proceed with caution",
                    extra={"job_id": job_id, "true_match_pairs_found": len(true_pairs)}
                )

            non_iter: typing.Iterator[typing.Tuple[typing.Tuple[dict, dict], int]] = (
                mpi_service.generate_non_match_tuning_samples(
                    session,
                    sample_size=job.params.non_match_sample_requested,
                    n_pairs=job.params.non_match_pairs_requested,
                )
            )
            non_pairs: list[typing.Tuple[dict, dict]] = []
            sample_used: int = 0
            for pair, found in non_iter:
                non_pairs.append(pair)
                if not sample_used:
                    sample_used = found
            if sample_used < 50000:
                LOGGER.warning(
                    "Lower than recommended negative sample used, proceed with caution",
                    extra={"job_id": job_id, "negative_sample_used": sample_used}
                )
            if len(non_pairs) < 3000:
                LOGGER.warning(
                    "Fewer than recommended non-match pairs found in MPI, proceed with caution",
                    extra={"job_id": job_id, "non_match_pairs_found": len(non_pairs)}
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
                schemas.LogOdd(feature=schemas.Feature.parse(k), value=v)
                for k, v in log_odds.items()
            ]

            # Step 4: Compute suggested RMS possible match window boundaries
            obj: models.Algorithm | None = default_algorithm(session)
            if obj is not None:
                algorithm: schemas.Algorithm = schemas.Algorithm.model_validate(obj)
                sorted_scores: dict[str, typing.Tuple[list[float], list[float]]] = (
                    prob_calc.calculate_and_sort_tuning_scores(
                        true_pairs, non_pairs, log_odds, algorithm
                    )
                )
                rms_bounds: dict[str, typing.Tuple[float, float]] = (
                    prob_calc.estimate_rms_bounds(sorted_scores)
                )
                pass_recs: list[schemas.PassRecommendation] = []
                for idx, algorithm_pass in enumerate(algorithm.passes):
                    pass_name: str = algorithm_pass.label or f"pass_{idx}"  # type: ignore
                    rec = schemas.PassRecommendation(
                        algorithm_label=algorithm.label,
                        pass_label=pass_name,
                        recommended_match_window=rms_bounds[pass_name]
                    )
                    pass_recs.append(rec)
                results.passes = pass_recs
            # Can only make recommendation if default algo exists, otherwise warn and skip
            else:
                LOGGER.warning(
                    "No default algorithm stored on-file, omitting RMS bound estimation",
                    extra={"job_id": job_id}
                )

            tuning_service.update_job(session, job, models.TuningStatus.COMPLETED, results)
        except Exception as exc:
            LOGGER.error(
                "tuning job failed", extra={"job_id": job_id, "exc": str(exc)}, exc_info=True
            )
            tuning_service.fail_job(session, job_id, str(exc))

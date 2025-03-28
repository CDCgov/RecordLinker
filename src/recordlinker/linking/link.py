"""
recordlinker.linking.link
~~~~~~~~~~~~~~~~~~~~~~~~~

This module is used to run the linkage algorithm using the MPI service
"""

import collections
import dataclasses
import logging
import typing

from sqlalchemy import orm

from recordlinker import models
from recordlinker import schemas
from recordlinker.database import mpi_service
from recordlinker.utils.mock import MockTracer

LOGGER = logging.getLogger(__name__)
TRACER: typing.Any = None
try:
    from opentelemetry import trace

    TRACER = trace.get_tracer(__name__)
except ImportError:
    # OpenTelemetry is an optional dependency, if its not installed use a mock tracer
    TRACER = MockTracer()


@dataclasses.dataclass
class LinkResult:
    person: models.Person
    belongingness_ratio: float


def compare(
    record: schemas.PIIRecord,
    patient: models.Patient,
    max_log_odds_points: float,
    max_allowed_missingness_proportion: float,
    missing_field_points_proportion: float,
    algorithm_pass: models.AlgorithmPass,
    log_odds_weights: dict[str, float],
) -> bool:
    """
    Compare the incoming record to the linked patient and return the calculated
    evaluation score. If a proportion of score points is accumulated via comparisons
    with missing fields that is above a user-defined threshold, automatically reject
    the potential match candidacy of the linked patient.

    :param record: The new, incoming record, as a PIIRecord data type.
    :param patient: A candidate record returned by blocking from the MPI, whose
      match quality the function call will evaluate.
    :param max_log_odds_points: The maximum available log odds points that can be
      accumulated by a candidate pair during this pass of the algorithm.
    :param max_allowed_missingness_proportion: The maximum proportion of log-odds
      weights that can be missing across all fields used in evaluating this pass.
    :param missing_field_points_proportion: The proportion of log-odds points
      that a field missing data will earn during comparison (i.e. a fraction of
      its regular log-odds weight value).
    :algorithm_pass: A data structure containing information about the pass of
      the algorithm in which this comparison is being run. Holds information
      like which fields to evaluate and how to total log-odds points.
    :param log_odds_weights: A dictionary mapping Field names to float values,
      which are the precomputed log-odds weights associated with that field.
    :returns: A boolean indicating whether the incoming record and the supplied
      candidate are a match, as determined by the specific matching rule
      contained in the algorithm_pass object.
    """
    # all the functions used for comparison
    evals: list[models.BoundEvaluator] = algorithm_pass.bound_evaluators()
    # a function to determine a match based on the comparison results
    matching_rule: typing.Callable = algorithm_pass.bound_rule()
    # keyword arguments to pass to comparison functions and matching rule
    kwargs: dict[typing.Any, typing.Any] = algorithm_pass.kwargs

    missing_field_weights = 0.0
    results: list[float] = []
    details: dict[str, typing.Any] = {"patient.reference_id": str(patient.reference_id)}
    for e in evals:
        # TODO: can we do this check earlier?
        feature = schemas.Feature.parse(e.feature)
        if feature is None:
            raise ValueError(f"Invalid comparison field: {e.feature}")

        # Evaluate the comparison function, track missingness, and append the
        # score component to the list
        result: tuple[float, bool] = e.func(
            record, patient, feature, missing_field_points_proportion, **kwargs
        )  # type: ignore
        if result[1]:
            # The field was missing, so update the running tally of how much
            # the candidate is missing overall
            missing_field_weights += log_odds_weights[str(feature.attribute)]
        results.append(result[0])
        details[f"evaluator.{e.feature}.{e.func.__name__}.result"] = result

    # Make sure this score wasn't just accumulated with missing checks
    if missing_field_weights <= max_allowed_missingness_proportion * max_log_odds_points:
        is_match = matching_rule(results, **kwargs)
    else:
        is_match = False
    details[f"rule.{matching_rule.__name__}.results"] = is_match
    # TODO: this may add a lot of noise, consider moving to debug
    LOGGER.info("patient comparison", extra=details)
    return is_match


def link_record_against_mpi(
    record: schemas.PIIRecord,
    session: orm.Session,
    algorithm: models.Algorithm,
    external_person_id: typing.Optional[str] = None,
    persist: bool = True,
) -> tuple[models.Patient | None, models.Person | None, list[LinkResult], schemas.Prediction]:
    """
    Runs record linkage on a single incoming record (extracted from a FHIR
    bundle) using an existing database as an MPI. Uses a flexible algorithm
    configuration to allow customization of the exact kind of linkage to
    run. Linkage is assumed to run using cluster membership (i.e. the new
    record must match a certain proportion of existing records all assigned
    to a person in order to match), and if multiple persons are matched,
    the new record is linked to the person with the strongest membership
    percentage.

    :param record: The PIIRecord to try to match to
      other records in the MPI.
    :param session: The SQLAlchemy session to use for database operations.
    :param algorithm: An algorithm configuration object
    :param external_person_id: An optional external identifier for the person
    :param persist: Whether to save the new patient record to the database
    :returns: A tuple consisting of a boolean indicating whether a match
      was found for the new record in the MPI, followed by the ID of the
      Person entity now associated with the incoming patient (either a
      new Person ID or the ID of an existing matched Person).
    """
    # Membership scores need to persist across linkage passes so that we can
    # find the highest scoring match across all passes
    scores: dict[models.Person, float] = collections.defaultdict(float)
    # the minimum ratio of matches needed to be considered a cluster member
    belongingness_ratio_lower_bound, belongingness_ratio_upper_bound = algorithm.belongingness_ratio
    # proportions for missingness calculation: points awarded, and max allowed
    missing_field_points_proportion = algorithm.missing_field_points_proportion
    max_missing_allowed_proportion = algorithm.max_missing_allowed_proportion
    # initialize counters to track evaluation results to log
    result_counts: dict[str, int] = {
        "persons_compared": 0,
        "patients_compared": 0,
        "above_lower_bound": 0,
        "above_upper_bound": 0,
    }
    for algorithm_pass in algorithm.passes:
        with TRACER.start_as_current_span("link.pass"):
            # Determine the maximum possible number of log-odds points in this pass
            evaluators: list[str] = [e["feature"] for e in algorithm_pass.evaluators]
            log_odds_points = algorithm_pass.kwargs["log_odds"]
            max_points = sum([log_odds_points[e] for e in evaluators])

            # initialize a dictionary to hold the clusters of patients for each person
            clusters: dict[models.Person, list[models.Patient]] = collections.defaultdict(list)
            # block on the pii_record and the algorithm's blocking criteria, then
            # iterate over the patients, grouping them by person
            with TRACER.start_as_current_span("link.block"):
                # get all candidate Patient records identified in blocking
                # and the remaining Patient records in their Person clusters
                pats = mpi_service.BlockData.get(
                    session, record, algorithm_pass, max_missing_allowed_proportion
                )
                for pat in pats:
                    clusters[pat.person].append(pat)

            # evaluate each Person cluster to see if the incoming record is a match
            with TRACER.start_as_current_span("link.evaluate"):
                for person, pats in clusters.items():
                    assert pats, "Patient cluster should not be empty"
                    matched_count = 0
                    for pat in pats:
                        # increment our match count if the pii_record matches the patient
                        with TRACER.start_as_current_span("link.compare"):
                            if compare(
                                record,
                                pat,
                                max_points,
                                max_missing_allowed_proportion,
                                missing_field_points_proportion,
                                algorithm_pass,
                                log_odds_points,
                            ):
                                matched_count += 1
                    result_counts["persons_compared"] += 1
                    result_counts["patients_compared"] += len(pats)
                    # calculate the match ratio for this person cluster
                    belongingness_ratio = matched_count / len(pats)
                    LOGGER.info(
                        "cluster belongingness",
                        extra={
                            "belongingness_ratio": belongingness_ratio,
                            "person.reference_id": str(person.reference_id),
                            "matched": matched_count,
                            "total": len(pats),
                            "algorithm.belongingness_ratio_lower": belongingness_ratio_lower_bound,
                            "algorithm.belongingness_ratio_upper": belongingness_ratio_upper_bound,
                        },
                    )
                    if belongingness_ratio >= belongingness_ratio_lower_bound:
                        # The match ratio is larger than the minimum cluster threshold,
                        # optionally update the max score for this person
                        scores[person] = max(scores[person], belongingness_ratio)

    prediction: schemas.Prediction = "possible_match"
    matched_person: typing.Optional[models.Person] = None
    results: list[LinkResult] = [
        LinkResult(k, v) for k, v in sorted(scores.items(), reverse=True, key=lambda i: i[1])
    ]
    result_counts["above_lower_bound"] = len(results)
    if not results:
        # No match
        prediction = "no_match"
        if persist:
            # Only create a new person cluster if we are persisting data
            matched_person = models.Person()
    elif results[0].belongingness_ratio >= belongingness_ratio_upper_bound:
        # Match (1 or many)
        prediction = "match"
        matched_person = results[0].person
        # reduce results to only those that meet the upper bound threshold
        results = [x for x in results if x.belongingness_ratio >= belongingness_ratio_upper_bound]
        result_counts["above_upper_bound"] = len(results)
        if not algorithm.include_multiple_matches:
            # reduce results to only the highest match
            results = [results[0]]

    patient: typing.Optional[models.Patient] = None
    if persist:
        with TRACER.start_as_current_span("insert"):
            patient = mpi_service.insert_patient(
                session,
                record,
                matched_person,
                record.external_id,
                external_person_id,
                commit=False,
            )

    LOGGER.info(
        "link results",
        extra={
            "person.reference_id": matched_person and str(matched_person.reference_id),
            "patient.reference_id": patient and str(patient.reference_id),
            "result.prediction": prediction,
            "result.count_patients_compared": result_counts["patients_compared"],
            "result.count_persons_above_lower": result_counts["above_lower_bound"],
            "result.count_persons_above_upper": result_counts["above_upper_bound"],
        },
    )

    # return a tuple indicating whether a match was found and the person ID
    return (patient, matched_person, results, prediction)

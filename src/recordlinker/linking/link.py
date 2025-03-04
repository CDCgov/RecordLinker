"""
recordlinker.linking.link
~~~~~~~~~~~~~~~~~~~~~~~~~

This module is used to run the linkage algorithm using the MPI service
"""

import collections
import dataclasses
import logging
import statistics
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
    """
    A data class designed to represent a single row of the "score tracking" table
    construct, as well as to capture the result of a single linkage to a Person
    cluster. Instance variables help define the scoring parameters used to 
    evaluate match strength. Result rows handle their own updates (e.g. when
    to update relative match score strengths as well as prioritizing certain
    matches over possible matches).
    """
    person: models.Person
    accumulated_points: float
    rms: float
    mmt: float
    cmt: float
    grade: str

    def _do_update(self, earned_points, rms, mmt, cmt, grade):
        """
        Helper function to abstract variable update setting to leave
        case-based logic clearer.
        """
        self.accumulated_points = earned_points
        self.rms = rms
        self.grade = grade
        self.cmt = cmt
        self.mmt = mmt
    
    def handle_update(self, earned_points, rms, mmt, cmt, grade):
        """
        Dynamically perform and handle any updates that should be tracked for
        the results of this Person cluster in linking. Updates must consider
        both match grade and RMS.

        1. If both grades (previously seen and newly processed) are equal,
        updating is easy: just take the result with the higher RMS.
        2. If the existing grade is certain but the new grade is not, we
        *don't* update: being above the Certain Match Threshold is a stricter
        inequality than being within the Possible Match Window, so we don't 
        want to overwrite with less information (Example: suppose the DIBBs
        algorithm passes were switched. Suppose Cluster A had an RMS of 0.918.
        This would be a match grade of 'certain'. If Pass 1 ran after Pass 2,
        and Cluster A scored an RMS of 0.922, that would grade as 'possible'.
        But despite the higher RMS, Cluster A actually accumualted more points
        and stronger separation already, so we don't want to downgrade.)
        3. If the new grade is certain but the existing grade is not, we
        *always* update. Being a 'certain' match is a stronger statement and
        thus more worth saving. Consider the example above with the passes
        as normal. It would be better to save the Pass 2 RMS of 0.918 that 
        graded as 'Certain' than it would be to keep the Pass 1 RMS of 0.922
        that only graded 'Possible,' since the user's previous profiling found
        these matches higher quality.        
        """
        # Start with the easy case: both grades are the same, so use the RMS
        if grade == self.grade:
            if rms > self.rms:
                self._do_update(earned_points, rms, mmt, cmt, grade)
        
        # Case 2: existing grade is certain, and since grades didn't enter
        # the equality if, new grade is only possible
        elif self.grade == 'certain':
            pass

        # Case 3: new grade is certain, and since grades didn't enter the 
        # equality if, existing grade is only possible
        elif grade == 'certain':
            self._do_update(earned_points, rms, mmt, cmt, grade)


def compare(
    record: schemas.PIIRecord, patient: models.Patient, algorithm_pass: models.AlgorithmPass
) -> float:
    """
    Compare the incoming record to the linked patient and return the calculated
    evaluation score.
    """
    # all the functions used for comparison
    evals: list[models.BoundEvaluator] = algorithm_pass.bound_evaluators()
    # a function to determine a match based on the comparison results
    matching_rule: typing.Callable = algorithm_pass.bound_rule()
    # keyword arguments to pass to comparison functions and matching rule
    kwargs: dict[typing.Any, typing.Any] = algorithm_pass.kwargs

    results: list[float] = []
    details: dict[str, typing.Any] = {"patient.reference_id": str(patient.reference_id)}
    for e in evals:
        # TODO: can we do this check earlier?
        feature = schemas.Feature.parse(e.feature)
        if feature is None:
            raise ValueError(f"Invalid comparison field: {e.feature}")
        # Evaluate the comparison function and append the result to the list
        result: float = e.func(record, patient, feature, **kwargs)  # type: ignore
        results.append(result)
        details[f"evaluator.{e.feature}.{e.func.__name__}.result"] = result
    
    rule_result = matching_rule(results, **kwargs)
    details[f"rule.{matching_rule.__name__}.results"] = rule_result
    # TODO: this may add a lot of noise, consider moving to debug
    LOGGER.info("patient comparison", extra=details)
    return rule_result


def grade_result(rms: float, mmt: float, cmt: float) -> str:
    """
    Helper function to assign a match-grade (derived from FHIR spec terminology)
    to a linkage result based on whether the result's match strength falls in 
    relation to the reference window (minimum_threshold, certain_threshold).
    """
    if rms < mmt:
        return "certainly-not"
    elif rms < cmt:
        return "possible"
    return "certain"


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
    scores: dict[models.Person, LinkResult] = {}
    # initialize counters to track evaluation results to log
    result_counts: dict[str, int] = {
        "persons_compared": 0,
        "patients_compared": 0,
    }
    for algorithm_pass in algorithm.passes:
        with TRACER.start_as_current_span("link.pass"):
            minimum_match_threshold, certain_match_threshold = algorithm_pass.possible_match_window

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
                # NOTE: need to remove patients with non-empty wrong blocking fields
                pats = mpi_service.get_block_data(session, record, algorithm_pass)
                for pat in pats:
                    clusters[pat.person].append(pat)

            # evaluate each Person cluster to see if the incoming record is a match
            with TRACER.start_as_current_span("link.evaluate"):
                for person, pats in clusters.items():
                    assert pats, "Patient cluster should not be empty"
                    log_odds_sums = []
                    for pat in pats:
                        with TRACER.start_as_current_span("link.compare"):
                            # track the accumulated points so we can eventually find
                            # the median and normalize it
                            rule_result = compare(record, pat, algorithm_pass)
                            log_odds_sums.append(rule_result)

                    result_counts["persons_compared"] += 1
                    result_counts["patients_compared"] += len(pats)
                    # calculate the relative match score for this person cluster
                    cluster_median = statistics.median(log_odds_sums)
                    rms = cluster_median / max_points
                    match_grade = grade_result(rms, minimum_match_threshold, certain_match_threshold)

                    LOGGER.info(
                        "cluster statistics",
                        extra={
                            "median log-odds points accumulated": cluster_median,
                            "relative match score": rms,
                            "person.reference_id": str(person.reference_id),
                            "patients compared in cluster": len(pats),
                            "algorithm.minimum_match_threshold": minimum_match_threshold,
                            "algorithm.certain_match_threshold": certain_match_threshold,
                        },
                    )
                    # The match strength must be above the minimum user threshold in order
                    # for this cluster to be worth remembering
                    if rms >= minimum_match_threshold:
                        if person not in scores:
                            scores[person] = LinkResult(
                                person,
                                cluster_median,
                                rms,
                                minimum_match_threshold,
                                certain_match_threshold,
                                match_grade
                            )
                        # Let the dynamic programming table track its own updates
                        scores[person].handle_update(
                            cluster_median, rms, minimum_match_threshold, certain_match_threshold, match_grade
                        )
    
    results: list[LinkResult] = sorted(scores.values(), reverse=True, key=lambda x: x.rms)
    certain_results = [x for x in results if x.grade == 'certain']
    # re-assign the results array since we already have the higher-priority
    # 'certain' grades if we need them
    results = [x for x in results if x.grade == 'possible']
    prediction: schemas.Prediction = "possible"
    matched_person: typing.Optional[models.Person] = None

    if not results and not certain_results:
        # No match
        prediction = "certainly-not"
        if persist:
            # Only create a new person cluster if we are persisting data
            matched_person = models.Person()

    elif certain_results and len(certain_results) > 0:
        # Match (1 or many)
        prediction = "certain"
        matched_person = certain_results[0].person
        if not algorithm.include_multiple_matches:
            # reduce results to only the highest match
            results = [certain_results[0]]
        else:
            # make sure we return all the actual 'certain' matches
            results = certain_results

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

    # Put together some strings to report the result, window, and interpretation
    # to the user; we don't save certainly-not grades in the dynamic table
    best_score_str: str = "n/a"
    reference_range: str = "n/a"
    if prediction == "certain":
        best_score_str = str(certain_results[0].rms)
        reference_range = "(" + str(certain_results[0].mmt) + ", " + str(certain_results[0].cmt) + ")"
    elif prediction == "possible":
        best_score_str = str(results[0].rms)
        reference_range = "(" + str(results[0].mmt) + ", " + str(results[0].cmt) + ")"
    LOGGER.info(
        "final linkage results",
        extra={
            "person.reference_id": matched_person and str(matched_person.reference_id),
            "patient.reference_id": patient and str(patient.reference_id),
            "result.prediction": prediction,
            "result.best_match_score": best_score_str,
            "result.best_match_reference_window": reference_range,
            "result.count_patients_compared": result_counts["patients_compared"],
        },
    )
    # return a tuple indicating whether a match was found and the person ID
    return (patient, matched_person, results, prediction)

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

from . import skip_values as sv

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
    pass_label: str
    rms: float
    mmt: float
    cmt: float
    match_grade: schemas.MatchGrade
    median_features: dict[str, float]

    def _update_score_tracking_row(self, earned_points, pass_lbl, rms, mmt, cmt, grade, median_features):
        """
        Helper function to abstract variable update setting to leave
        case-based logic clearer.
        """
        self.accumulated_points = earned_points
        self.pass_label = pass_lbl
        self.rms = rms
        self.match_grade = grade
        self.cmt = cmt
        self.mmt = mmt
        self.median_features = median_features

    def check_and_update_score(self, earned_points, pass_lbl, rms, mmt, cmt, grade, median_features):
        """
        Dynamically perform and handle any updates that should be tracked for
        the results of this Person cluster in linking. Updates must consider
        both match grade and RMS.

        1. If both grades (previously seen and newly processed) are equal,
        we take the result with the higher RMS.
        2. If the existing grade is certain but the new grade is not, we
        *don't* update, since each pass is an indepedent match test.
        3. If the new grade is certain but the existing grade is not, we
        *always* update.
        """
        # Start with the easy case: both grades are the same, so use the RMS
        if grade == self.match_grade:
            if rms > self.rms:
                self._update_score_tracking_row(earned_points, pass_lbl, rms, mmt, cmt, grade, median_features)

        # Case 2: existing grade is certain, and since grades didn't enter
        # the equality if, new grade is only possible
        elif self.match_grade == "certain":
            pass

        # Case 3: new grade is certain, and since grades didn't enter the
        # equality if, existing grade is only possible
        elif grade == "certain":
            self._update_score_tracking_row(earned_points, pass_lbl, rms, mmt, cmt, grade, median_features)


def invoke_evaluator(
    evaluator: schemas.Evaluator,
    record: schemas.PIIRecord,
    mpi_record: schemas.PIIRecord,
    context: schemas.AlgorithmContext,
) -> tuple[float, bool]:
    """
    Invoke the evaluator function and return the result
    """
    fn: typing.Callable = evaluator.func.callable()
    kwargs = {
        "log_odds": context.get_log_odds(evaluator.feature) or 0.0,
        "missing_field_points_proportion": context.advanced.missing_field_points_proportion,
        "fuzzy_match_threshold": evaluator.fuzzy_match_threshold
        or context.advanced.fuzzy_match_threshold,
        "fuzzy_match_measure": evaluator.fuzzy_match_measure
        or context.advanced.fuzzy_match_measure,
    }
    return fn(record, mpi_record, evaluator.feature, **kwargs)


def compare(
    record: schemas.PIIRecord,
    mpi_record: schemas.PIIRecord,
    algorithm_pass: schemas.AlgorithmPass,
    context: schemas.AlgorithmContext,
) -> typing.Tuple[float, dict[str, float]]:
    """
    Compare the incoming record to the linked patient and return the calculated
    evaluation score. If a proportion of score points is accumulated via comparisons
    with missing fields that is above a user-defined threshold, automatically reject
    the potential match candidacy of the linked patient.

    :param record: The new, incoming record, as a PIIRecord data type.
    :param mpi_record: A candidate record returned by blocking from the MPI, whose
      match quality the function call will evaluate.
    :algorithm_pass: A data structure containing information about the pass of
      the algorithm in which this comparison is being run. Holds information
      like which fields to evaluate and how to total log-odds points.
    :context: A AlgorithmContext data structure containing data about the algorithm
    :returns: A boolean indicating whether the incoming record and the supplied
      candidate are a match, as determined by the specific matching rule
      contained in the algorithm_pass object.
    """
    missing_field_weights: float = 0.0
    results: list[float] = []
    details: dict[str, typing.Any] = {}
    max_log_odds_points: float = 0.0
    max_missing_proportion: float = context.advanced.max_missing_allowed_proportion
    feature_scores: dict[str, float] = collections.defaultdict(float)
    for evaluator in algorithm_pass.evaluators:
        log_odds: float = context.get_log_odds(evaluator.feature) or 0.0
        max_log_odds_points += log_odds
        # Evaluate the comparison function, track missingness, and append the
        # score component to the list
        result: tuple[float, bool] = invoke_evaluator(evaluator, record, mpi_record, context)
        if result[1]:
            # The field was missing, so update the running tally of how much
            # the candidate is missing overall
            missing_field_weights += log_odds
        results.append(result[0])
        feature_scores[str(evaluator.feature)] = result[0]
        details[f"evaluator.{evaluator.feature}.{evaluator.func}.result"] = result

    # Make sure this score wasn't just accumulated with missing checks
    if missing_field_weights <= (max_missing_proportion * max_log_odds_points):
        rule_result = sum(results)
    else:
        rule_result = 0.0
    details["rule.probabilistic_sum.results"] = rule_result
    # TODO: this may add a lot of noise, consider moving to debug
    LOGGER.info("patient comparison", extra=details)
    return rule_result, feature_scores


def grade_rms(rms: float, mmt: float, cmt: float) -> schemas.MatchGrade:
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
    algorithm: schemas.Algorithm,
    external_person_id: typing.Optional[str] = None,
    persist: bool = True,
) -> tuple[models.Patient | None, models.Person | None, list[LinkResult], schemas.MatchGrade]:
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
    # get the algorithm context
    context: schemas.AlgorithmContext = algorithm.algorithm_context

    # initialize counters to track evaluation results to log
    result_counts: dict[str, int] = {
        "persons_compared": 0,
        "patients_compared": 0,
    }
    # clean the incoming record
    cleaned_record: schemas.PIIRecord = sv.remove_skip_values(record, context.skip_values)
    for idx, algorithm_pass in enumerate(algorithm.passes):
        with TRACER.start_as_current_span("link.pass"):
            pass_label = algorithm_pass.label or f"pass_{idx}"
            minimum_match_threshold, certain_match_threshold = algorithm_pass.possible_match_window
            # Determine the maximum possible number of log-odds points in this pass
            max_points: float = sum(
                [context.get_log_odds(e.feature) or 0.0 for e in algorithm_pass.evaluators]
            )

            # initialize a dictionary to hold the clusters of patients for each person
            clusters: dict[models.Person, list[schemas.PIIRecord]] = collections.defaultdict(list)

            # block on the cleaned_record and the algorithm's blocking criteria, then
            # iterate over the patients, grouping them by person
            with TRACER.start_as_current_span("link.block"):
                # get all candidate Patient records identified in blocking
                # and the remaining Patient records in their Person clusters
                pats = mpi_service.BlockData.get(session, cleaned_record, algorithm_pass, context)
                for pat in pats:
                    # convert the Patient model into a cleaned PIIRecord for comparison
                    mpi_record: schemas.PIIRecord = sv.remove_skip_values(
                        schemas.PIIRecord.from_patient(pat), context.skip_values
                    )
                    clusters[pat.person].append(mpi_record)

            # evaluate each Person cluster to see if the incoming record is a match
            with TRACER.start_as_current_span("link.evaluate"):
                for person, mpi_records in clusters.items():
                    assert mpi_records, "Patient cluster should not be empty"
                    log_odds_sums = []
                    feature_scores_dicts = []
                    for mpi_record in mpi_records:
                        with TRACER.start_as_current_span("link.compare"):
                            # track the accumulated points so we can eventually find
                            # the median and normalize it
                            rule_result, feature_scores = compare(
                                record,
                                mpi_record,
                                algorithm_pass,
                                context,
                            )
                            log_odds_sums.append(rule_result)
                            feature_scores_dicts.append(feature_scores)

                    result_counts["persons_compared"] += 1
                    result_counts["patients_compared"] += len(mpi_records)
                    # Calculate median feature contributions from each match
                    median_features = {}
                    for e in algorithm_pass.evaluators:
                        median_features[str(e.feature)] = statistics.median([fd[str(e.feature)] for fd in feature_scores_dicts])
                    # Calculate the relative match score for this person cluster
                    cluster_median = statistics.median(log_odds_sums)
                    rms = cluster_median / max_points
                    match_grade = grade_rms(rms, minimum_match_threshold, certain_match_threshold)

                    LOGGER.info(
                        "cluster statistics",
                        extra={
                            "median log-odds points accumulated": cluster_median,
                            "relative match score": rms,
                            "person.reference_id": str(person.reference_id),
                            "patients compared in cluster": len(mpi_records),
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
                                pass_label,
                                rms,
                                minimum_match_threshold,
                                certain_match_threshold,
                                match_grade,
                                median_features
                            )
                        # Let the dynamic programming table track its own updates
                        scores[person].check_and_update_score(
                            cluster_median,
                            pass_label,
                            rms,
                            minimum_match_threshold,
                            certain_match_threshold,
                            match_grade,
                            median_features
                        )

    results: list[LinkResult] = sorted(scores.values(), reverse=True, key=lambda x: x.rms)
    certain_results = [x for x in results if x.match_grade == "certain"]
    # re-assign the results array since we already have the higher-priority
    # 'certain' grades if we need them; we return the `results` variable as
    # a placeholder later, so we need to keep this around for re-assignment
    results = [x for x in results if x.match_grade == "possible"]
    final_grade: schemas.MatchGrade = "possible"
    matched_person: typing.Optional[models.Person] = None

    if not results and not certain_results:
        # No match
        final_grade = "certainly-not"
        if persist:
            # Only create a new person cluster if we are persisting data
            matched_person = models.Person()

    elif certain_results and len(certain_results) > 0:
        # Match (1 or many)
        final_grade = "certain"
        matched_person = certain_results[0].person
        if not context.include_multiple_matches:
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
    matching_pass_label: str = "n/a"
    if final_grade == "certain":
        best_score_str = str(certain_results[0].rms)
        reference_range = f"({certain_results[0].mmt}, {certain_results[0].cmt})"
        matching_pass_label = certain_results[0].pass_label
    elif final_grade == "possible":
        best_score_str = str(results[0].rms)
        reference_range = f"({results[0].mmt}, {results[0].cmt})"
        matching_pass_label = results[0].pass_label
    LOGGER.info(
        "final linkage results",
        extra={
            "person.reference_id": matched_person and str(matched_person.reference_id),
            "patient.reference_id": patient and str(patient.reference_id),
            "result.match_grade": final_grade,
            "result.best_match_score": best_score_str,
            "result.label_of_matching_pass": matching_pass_label,
            "result.best_match_reference_window": reference_range,
            "result.count_patients_compared": result_counts["patients_compared"],
        },
    )
    # return a tuple indicating whether a match was found and the person ID
    return (patient, matched_person, results, final_grade)

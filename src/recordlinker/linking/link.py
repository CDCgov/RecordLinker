"""
recordlinker.linking.link
~~~~~~~~~~~~~~~~~~~~~~~~~

This module is used to run the linkage algorithm using the MPI service
"""

import collections
import typing
import uuid

from sqlalchemy import orm

from recordlinker import models
from recordlinker import schemas
from recordlinker.database import mpi_service

from . import matchers

TRACER: typing.Any = None
try:
    from opentelemetry import trace

    TRACER = trace.get_tracer(__name__)
except ImportError:
    # OpenTelemetry is an optional dependency, if its not installed use a mock tracer
    from recordlinker.utils.mock import MockTracer

    TRACER = MockTracer()


def compare(
    record: schemas.PIIRecord, patient: models.Patient, algorithm_pass: models.AlgorithmPass
) -> bool:
    """
    Compare the incoming record to the linked patient
    """
    # all the functions used for comparison
    funcs: dict[str, matchers.FEATURE_COMPARE_FUNC] = algorithm_pass.bound_evaluators()
    # a function to determine a match based on the comparison results
    matching_rule: matchers.MATCH_RULE_FUNC = algorithm_pass.bound_rule()
    # keyword arguments to pass to comparison functions and matching rule
    kwargs: dict[typing.Any, typing.Any] = algorithm_pass.kwargs

    results: list[float] = []
    for field, func in funcs.items():
        # TODO: can we do this check earlier?
        feature = getattr(schemas.Feature, field, None)
        if feature is None:
            raise ValueError(f"Invalid comparison field: {field}")
        # Evaluate the comparison function and append the result to the list
        result: float = func(record, patient, feature, **kwargs)  # type: ignore
        results.append(result)
    return matching_rule(results, **kwargs)  # type: ignore


def link_record_against_mpi(
    record: schemas.PIIRecord,
    session: orm.Session,
    algorithm: models.Algorithm,
    external_person_id: typing.Optional[str] = None,
) -> tuple[bool, uuid.UUID, uuid.UUID]:
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
    :returns: A tuple consisting of a boolean indicating whether a match
      was found for the new record in the MPI, followed by the ID of the
      Person entity now associated with the incoming patient (either a
      new Person ID or the ID of an existing matched Person).
    """
    # Membership scores need to persist across linkage passes so that we can
    # find the highest scoring match across all passes
    scores: dict[models.Person, float] = collections.defaultdict(float)
    for algorithm_pass in algorithm.passes:
        with TRACER.start_as_current_span("link.pass"):
            # the minimum ratio of matches needed to be considered a cluster member
            cluster_ratio = algorithm_pass.cluster_ratio
            # initialize a dictionary to hold the clusters of patients for each person
            clusters: dict[models.Person, list[models.Patient]] = collections.defaultdict(list)
            # block on the pii_record and the algorithm's blocking criteria, then
            # iterate over the patients, grouping them by person
            with TRACER.start_as_current_span("link.block"):
                # get all candidate Patient records identified in blocking
                # and the remaining Patient records in their Person clusters
                patients = mpi_service.get_block_data(session, record, algorithm_pass)
                for patient in patients:
                    clusters[patient.person].append(patient)

            # evaluate each Person cluster to see if the incoming record is a match
            with TRACER.start_as_current_span("link.evaluate"):
                for person, patients in clusters.items():
                    assert patients, "Patient cluster should not be empty"
                    matched_count = 0
                    for patient in patients:
                        # increment our match count if the pii_record matches the patient
                        with TRACER.start_as_current_span("link.compare"):
                            if compare(record, patient, algorithm_pass):
                                matched_count += 1
                    # calculate the match ratio for this person cluster
                    match_ratio = matched_count / len(patients)
                    if match_ratio >= cluster_ratio:
                        # The match ratio is larger than the minimum cluster threshold,
                        # optionally update the max score for this person
                        scores[person] = max(scores[person], match_ratio)

    matched_person: typing.Optional[models.Person] = None
    if scores:
        # Find the person with the highest matching score
        matched_person, _ = max(scores.items(), key=lambda i: i[1])

    with TRACER.start_as_current_span("insert"):
        patient = mpi_service.insert_patient(
            session,
            record,
            matched_person,
            record.external_id,
            external_person_id,
        )

    # return a tuple indicating whether a match was found and the person ID
    return (bool(matched_person), patient.person.reference_id, patient.reference_id)

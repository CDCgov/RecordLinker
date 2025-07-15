"""
recordlinker.linking.mpi_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides the data access functions to the MPI tables
"""

import itertools
import logging
import math
import random
import typing
import uuid

from sqlalchemy import bindparam
from sqlalchemy import exists
from sqlalchemy import insert
from sqlalchemy import literal
from sqlalchemy import orm
from sqlalchemy import select
from sqlalchemy.sql import expression

from recordlinker import models
from recordlinker import schemas

from . import get_random_function

LOGGER = logging.getLogger(__name__)


class BlockData:
    @classmethod
    def _ordered_odds(
        cls, keys: list[models.BlockingKey], context: schemas.AlgorithmContext
    ) -> dict[models.BlockingKey, float]:
        """
        Return a dictionary of key_ids ordered by log_odds values from highest to lowest.

        :param keys: list[BlockingKey]
        :param context: AlgorithmContext
        :return: dict[BlockingKey, float]
        """
        result: dict[models.BlockingKey, float] = {k: context.get_log_odds(k) or 0.0 for k in keys}
        return dict(sorted(result.items(), key=lambda item: item[1], reverse=True))

    @classmethod
    def _should_continue_blocking(
        cls, total_odds: float, missing_odds: float, max_missing_allowed_proportion: float
    ) -> bool:
        """
        Analyze the log odds of the blocking keys found in the query.  If the number of
        points missing is above the maximum allowed or no log odds were specified, return
        False to indicate this blocking query should be skipped.

        :param total_odds: float
        :param missing_odds: float
        :param max_missing_allowed_proportion: float
        :return: bool
        """
        if total_odds == 0:
            # No log odds were specified
            fn_params = {k: v for k, v in locals().items() if k != "cls"}
            LOGGER.info("skipping blocking query: no log odds", extra=fn_params)
            return False
        if total_odds and (missing_odds / total_odds) > max_missing_allowed_proportion:
            # The log odds for the missing blocking keys were above the minimum threshold
            fn_params = {k: v for k, v in locals().items() if k != "cls"}
            LOGGER.info("skipping blocking query: log odds too low", extra=fn_params)
            return False
        return True

    @classmethod
    def _filter_incorrect_match(
        cls, patient: models.Patient, blocking_values: dict[models.BlockingKey, list[str]]
    ) -> bool:
        """
        Filter out patient records that have conflicting blocking values with the incoming
        record.  If either record is missing values for a blocking key, we can ignore,
        however when both records have values, verify that there is overlap between
        the values.  Return False if the records are not in agreement.

        :param patient: models.Patient
        :param blocking_values: dict
        :return: bool
        """
        agree_count: int = 0
        mpi_record: schemas.PIIRecord = schemas.PIIRecord.from_patient(patient)
        for key, incoming_vals in blocking_values.items():
            if not incoming_vals:
                # The incoming record has no value for this blocking key, thus there
                # is no reason to compare.  We can increment the counter to indicate
                # the two records are still in agreement and continue
                agree_count += 1
                continue
            # Calculate the blocking values for the patient
            patient_vals = mpi_record.blocking_keys(key)
            if not patient_vals:
                # The patient record has no value for this blocking key, thus there
                # is no reason to compare.  We can increment the counter to indicate
                # the two records are still in agreement and continue
                agree_count += 1
                continue
            # Generator gets us best performance, fastest way to check membership
            # because we return True as soon as we get 1 rather than build the
            # whole list.
            if any(v in patient_vals for v in incoming_vals):
                agree_count += 1

        # If we get through all the blocking criteria with no missing entries
        # and no true-value agreement, we exclude
        return agree_count == len(blocking_values)

    @classmethod
    def get(
        cls,
        session: orm.Session,
        record: schemas.PIIRecord,
        algorithm_pass: schemas.AlgorithmPass,
        context: schemas.AlgorithmContext,
    ) -> typing.Sequence[models.Patient]:
        """
        Get all of the matching Patients for the given data using the provided
        blocking keys defined in the algorithm_pass. Also, get all the
        remaining Patient records in the Person clusters identified in
        blocking to calculate Belongingness Ratio.

        :param session: The database session
        :param record: The PIIRecord to match
        :param algorithm_pass: The AlgorithmPass to use
        :param context: The AlgorithmContext
        :return: The matching Patients
        """
        # Create the base query
        base: expression.Select = expression.select(models.Patient.person_id).distinct()
        # Get an ordered dict of blocking keys and their log odds
        key_odds = cls._ordered_odds(algorithm_pass.blocking_keys, context)
        # Total log odds from all blocking keys
        total_odds = sum(key_odds.values())
        # Total log odds for keys with missing values
        missing_odds: float = 0
        # Blocking key values
        blocking_values: dict[models.BlockingKey, list[str]] = {}
        # Build the join criteria, we are joining the Blocking Value table
        # multiple times, once for each Blocking Key.  If a Patient record
        # has a matching Blocking Value for all the Blocking Keys, then it
        # is considered a match.
        for idx, (key, log_odds) in enumerate(key_odds.items()):
            # Get all the possible values from the data for this key
            blocking_values[key] = [v for v in record.blocking_keys(key)]
            if not blocking_values[key]:
                # Add the missing log odds to the total and check if we should abort
                missing_odds += log_odds
                if not cls._should_continue_blocking(
                    total_odds, missing_odds, context.advanced.max_missing_allowed_proportion
                ):
                    return []
                # This key doesn't have values, skip the joining query
                continue
            # Create a dynamic alias for the Blocking Value table using the index
            # this is necessary since we are potentially joining the same table
            # multiple times with different conditions
            alias = orm.aliased(models.BlockingValue, name=f"bv{idx}")
            # Add a join clause to the mpi_blocking_value table for each Blocking Key.
            # This results in multiple joins to the same table, one for each Key, but
            # with different joining conditions.
            base = base.join(
                alias,
                expression.and_(
                    models.Patient.id == alias.patient_id,
                    alias.blockingkey == key.id,
                    alias.value.in_(blocking_values[key]),
                ),
            )

        # Using the subquery of unique Patient IDs, select all the Patients
        expr = expression.select(models.Patient).where(models.Patient.person_id.in_(base))
        # Execute the query and collect all the Patients in matching Person clusters
        patients: typing.Sequence[models.Patient] = session.execute(expr).scalars().all()
        # Remove any Patient records that have incorrect blocking value matches
        return [p for p in patients if cls._filter_incorrect_match(p, blocking_values)]


def insert_patient(
    session: orm.Session,
    record: schemas.PIIRecord,
    person: typing.Optional[models.Person] = None,
    external_patient_id: typing.Optional[str] = None,
    external_person_id: typing.Optional[str] = None,
    commit: bool = True,
) -> models.Patient:
    """
    Insert a new patient record into the database.

    :param session: The database session
    :param record: The PIIRecord to insert
    :param person: Optional Person to associate with the Patient
    :param external_patient_id: Optional external patient ID
    :param external_person_id: Optional external person ID
    :param commit: Whether to commit the transaction

    :returns: The inserted Patient record
    """

    patient = models.Patient(
        person=person, data=record.to_data(), external_patient_id=external_patient_id
    )

    if external_person_id is not None:
        patient.external_person_id = external_person_id
        patient.external_person_source = "IRIS"

    # create a new Patient record
    session.add(patient)
    session.flush()

    # insert blocking values
    insert_blocking_values(session, [patient], commit=False)

    if commit:
        session.commit()
    return patient


def bulk_insert_patients(
    session: orm.Session,
    records: typing.Sequence[schemas.PIIRecord],
    person: typing.Optional[models.Person] = None,
    external_person_id: typing.Optional[str] = None,
    commit: bool = True,
) -> typing.Sequence[models.Patient]:
    """
    Insert multiple patient records, associated with 1 Person, into the database.

    :param session: The database session
    :param records: The PIIRecords to insert
    :param person: Optional Person to associate with the Patients
    :param external_person_id: Optional external person ID to associate with the Patients
    :param commit: Whether to commit the transaction

    :returns: The inserted Patient records
    """
    if session.get_bind().dialect.name == "mysql":
        raise ValueError("Bulk insert not supported for MySQL")

    if not records:
        return []

    if person:
        session.add(person)
        session.flush()

    pat_data = [
        {
            "person_id": person and person.id,
            "data": record.to_data(),
            "external_patient_id": record.external_id,
            "external_person_id": external_person_id,
            "external_person_source": "IRIS" if external_person_id else None,
        }
        for record in records
    ]

    patients: typing.Sequence[models.Patient] = session.scalars(
        insert(models.Patient).returning(models.Patient, sort_by_parameter_order=True), pat_data
    ).all()

    insert_blocking_values(session, patients, records=records, commit=False)

    if commit:
        session.commit()
    return patients


def update_patient(
    session: orm.Session,
    patient: models.Patient,
    record: typing.Optional[schemas.PIIRecord] = None,
    person: typing.Optional[models.Person] = None,
    external_patient_id: typing.Optional[str] = None,
    commit: bool = True,
) -> models.Patient:
    """
    Updates an existing patient record in the database.

    :param session: The database session
    :param patient: The Patient to update
    :param record: Optional PIIRecord to update
    :param person: Optional Person to associate with the Patient
    :param external_patient_id: Optional external patient ID
    :param commit: Whether to commit the transaction

    :returns: The updated Patient record
    """
    if patient.id is None:
        raise ValueError("Patient has not yet been inserted into the database")

    if record:
        patient.data = record.to_data()
        delete_blocking_values_for_patient(session, patient, commit=False)
        insert_blocking_values(session, [patient], commit=False)

    if person:
        patient.person = person

    if external_patient_id is not None:
        patient.external_patient_id = external_patient_id

    session.flush()
    if commit:
        session.commit()
    return patient


def insert_blocking_values(
    session: orm.Session,
    patients: typing.Sequence[models.Patient],
    records: typing.Sequence[schemas.PIIRecord] | None = None,
    commit: bool = True,
) -> None:
    """
    Inserts BlockingValues for the Patients into the MPI database.

    :param session: The database session
    :param patients: The Patients to insert BlockingValues for
    :param records: Optional list of corresponding PIIRecords, for the patients.  If not provided, they
        will be retrieved from the Patient objects.
    :param commit: Whether to commit the transaction

    :returns: None
    """
    if records is not None and len(patients) != len(records):
        raise ValueError("Patients and records must be the same length")

    data: list[dict] = []
    for idx, patient in enumerate(patients):
        record = records[idx] if records else schemas.PIIRecord.from_patient(patient)
        for key, val in record.blocking_values():
            data.append({"patient_id": patient.id, "blockingkey": key.id, "value": val})
    if not data:
        return

    if session.get_bind().dialect.name == "mysql":
        # MySQL doesn't support bulk inserts, thus we need to insert
        # each row individually
        session.add_all([models.BlockingValue(**d) for d in data])
    else:
        # For all other dialects, we can use a bulk insert to improve performance
        session.execute(insert(models.BlockingValue), data)
    if commit:
        session.commit()


def delete_blocking_values_for_patient(
    session: orm.Session, patient: models.Patient, commit: bool = True
) -> None:
    """
    Delete all BlockingValues for a given Patient.

    :param session: The database session
    :param patient: The Patient to delete BlockingValues for
    :param commit: Whether to commit the transaction

    :returns: None
    """
    session.query(models.BlockingValue).filter(
        models.BlockingValue.patient_id == patient.id
    ).delete()

    if commit:
        session.commit()


def get_patients_by_reference_ids(
    session: orm.Session, *reference_ids: uuid.UUID
) -> list[models.Patient | None]:
    """
    Retrieve all the Patients by their reference ids. If a Patient is not found,
    a None value will be returned in the list for that reference id. Eagerly load
    the Person associated with the Patient.
    """
    query = (
        select(models.Patient)
        .where(models.Patient.reference_id.in_(reference_ids))
        .options(orm.joinedload(models.Patient.person))
    )

    patients_by_id: dict[uuid.UUID, models.Patient] = {
        patient.reference_id: patient for patient in session.execute(query).scalars().all()
    }
    return [patients_by_id.get(ref_id) for ref_id in reference_ids]


def get_person_by_reference_id(
    session: orm.Session, person_reference_id: uuid.UUID
) -> models.Person | None:
    """
    Retrieve a single Person by their person reference ID.
    """
    query = select(models.Person).where(models.Person.reference_id == person_reference_id)
    return session.scalar(query)


def get_persons_by_reference_ids(
    session: orm.Session, *person_reference_ids: uuid.UUID
) -> list[models.Person | None]:
    """
    Retrieve multiple Persons by their person reference IDs. If a Person is not found,
    a None value will be returned in the list for that reference id.
    """
    query = select(models.Person).where(models.Person.reference_id.in_(person_reference_ids))
    persons_by_reference_ids: dict[uuid.UUID, models.Person] = {
        person.reference_id: person for person in session.execute(query).scalars().all()
    }
    return [persons_by_reference_ids.get(ref_id) for ref_id in person_reference_ids]


def update_person_cluster(
    session: orm.Session,
    patients: typing.Sequence[models.Patient],
    person: models.Person | None = None,
    commit: bool = True,
) -> models.Person:
    """
    Update the cluster for a given patient.
    """
    person = person or models.Person()
    for patient in patients:
        patient.person = person
    session.flush()

    if commit:
        session.commit()
    return person


def update_patient_person_ids(
    session: orm.Session,
    person: models.Person,
    person_ids: typing.Sequence[int],
    commit: bool = True,
) -> models.Person:
    """
    Update the person_id for all Patients by current person_id.
    """
    session.query(models.Patient).filter(models.Patient.person_id.in_(person_ids)).update(
        {models.Patient.person_id: person.id}
    )
    if commit:
        session.commit()
    return person


def reset_mpi(session: orm.Session, commit: bool = True):
    """
    Reset the MPI database by deleting all Person and Patient records.
    """
    session.query(models.BlockingValue).delete()
    session.query(models.Patient).delete()
    session.query(models.Person).delete()
    if commit:
        session.commit()


def delete_patient(session: orm.Session, obj: models.Patient, commit: bool = False) -> None:
    """
    Deletes an Patient from the database

    :param session: The database session
    :param obj: The Patient to delete
    :param commit: Commit the transaction
    """
    delete_blocking_values_for_patient(session, obj, commit=False)
    session.delete(obj)
    if commit:
        session.commit()


def delete_persons(
    session: orm.Session, obj: typing.Sequence[models.Person], commit: bool = False
) -> None:
    """
    Deletes 1 or more Person from the database

    :param session: The database session
    :param obj: The Person(s) to delete
    :param commit: Commit the transaction
    """
    for person in obj:
        session.delete(person)
    if commit:
        session.commit()


def check_person_for_patients(session: orm.Session, person: models.Person) -> bool:
    """
    Check if a Person has at least 1 associated Patient.
    """
    query = select(literal(1)).filter(models.Patient.person_id == person.id).limit(1)
    return True if session.execute(query).scalar() is not None else False


def get_orphaned_patients(
    session: orm.Session,
    limit: int | None = 50,
    cursor: int | None = None,
) -> typing.Sequence[models.Patient]:
    """
    Retrieve orphaned Patients in the MPI database, up to the provided limit.
    """
    query = (
        select(models.Patient)
        .where(models.Patient.person_id.is_(None))
        .order_by(models.Patient.id)
        .limit(limit)
    )

    # Apply cursor if provided
    if cursor:
        query = query.where(models.Patient.id > cursor)

    return session.execute(query).scalars().all()


def get_orphaned_persons(
    session: orm.Session,
    limit: int | None = 50,
    cursor: int | None = None,
) -> typing.Sequence[models.Person]:
    """
    Retrieve orphaned Persons in the MPI database, up to the provided limit. If a
    cursor (in the form of a person reference_id) is provided, only retrieve Persons
    with a reference_id greater than the cursor.
    """
    # subquery to check if a Person has at least 1 associated Patient
    subquery = select(models.Patient.id).where(models.Patient.person_id == models.Person.id)

    # Main query using NOT EXISTS
    query = select(models.Person).where(~exists(subquery)).order_by(models.Person.id)

    if cursor:
        query = query.filter(models.Person.id > cursor)

    query = query.limit(
        limit
    )  # limit applied after cursor to ensure the limit is applied after the JOIN and starts from the cursor after the join

    return session.execute(query).scalars().all()


def generate_true_match_tuning_samples(
    session: orm.Session, n_pairs: int
) -> typing.Iterator[typing.Tuple[dict, dict]]:
    """
    Creates a sample of known "true match" pairs of patient records of
    size n_pairs using previously labeled data. Pairs of records are
    randomly sampled from randomly chosen person clusters until
    a list of unique pairs has been obtained.

    :param session: A database session to use for executing queries.
    :param n_pairs: The number of pairs of true-matches to generate.
    :returns An iterator of tuples containing pairs of patient data
      dictionaries.
    """
    p1 = orm.aliased(models.Patient, name="p1")
    p2 = orm.aliased(models.Patient, name="p2")
    random_pairs = (
        expression.select(p1.id.label("patient_1_id"), p2.id.label("patient_2_id"))
        .join_from(
            p1,
            p2,
            expression.and_(p1.person_id == p2.person_id, p1.id < p2.id, p1.person_id.isnot(None)),
        )
        .order_by(get_random_function(session.get_bind().dialect))
        .limit(n_pairs)
        .cte()
    )
    sample = (
        expression.select(
            p1.data.label("patient_data_1"),
            p2.data.label("patient_data_2"),
        )
        .join_from(random_pairs, p1, p1.id == random_pairs.c.patient_1_id)
        .join(p2, p2.id == random_pairs.c.patient_2_id)
    )

    for row in session.execute(sample):
        yield (row[0], row[1])


def generate_non_match_tuning_samples(
    session: orm.Session, sample_size: int, n_pairs: int
) -> typing.Iterator[typing.Tuple[typing.Tuple[dict, dict], int]]:
    """
    Creates a sample of known "non match" pairs of patient records of
    size n_pairs using previously labeled data. The complete collection
    of patient data is first randomly sub-sampled if there are more than
    100k patient rows (since a random sample from a random sample is
    equivalent to randomly sampling the first group), and then pairs
    are randomly generated until the desired number of non-matches is hit.

    :param session: A database session with which to execute queries.
    :param sample_size: The number of patient records to sub-sample from
      the MPI for use with combinatorial pairing. Effectively "shrinks"
      the scope of the world the function needs to consider, since
      randomly sampling out of a random sample is equivalent to randomly
      sampling from the initial population.
    :param n_pairs: The number of non-matching pairs to try to generate.
      The function's internal pairing loop (which performs random
      generation and checking) is bounded by a secondary stopping
      condition which may terminate before this number is hit (in order
      to prevent excessive time spent looping).
    :returns: An iterator tuple whose first element is a sequence of randomly
      sub-sampled pairs of non-matching records, and whose second element
      is the length of the sub-sample actually retrieved from the DB
      from which these pairs were generated.
    """
    # First, sanity check that we have a big enough sample size to grab
    # the requested number of pairs in "reasonable" time--use the
    # Taylor approximation for e^x derived from the Birthday Problem
    if sample_size == 1:
        raise ValueError("Cannot sample from a single database point")
    taylor_expansion = math.exp(
        (-1.0 * n_pairs * (n_pairs - 1.0)) / (sample_size * (sample_size - 1.0))
    )
    repeat_probability = 1.0 - taylor_expansion
    if repeat_probability >= 0.5:
        raise ValueError("Too many pairs requested for sample size")

    random_ids: list[int] = [
        row[0]
        for row in session.query(models.Patient.id)
        .order_by(get_random_function(session.get_bind().dialect))
        .limit(sample_size)
        .all()
    ]
    query: expression.Select = (
        select(models.Patient.id, models.Patient.person_id, models.Patient.data)
       .where(models.Patient.id.in_(bindparam("ids", expanding=True)))
    )

    already_seen: set[tuple[int, int]] = set()
    num_iters: int = 0
    num_pairs: int = 0
    found_size: int = len(random_ids)
    while True:
        ids: list[int] = random.choices(random_ids, k=100)
        # iterate over the query, pulling out the first two items at a time
        for pair_1, pair_2 in itertools.pairwise(session.execute(query, {"ids": ids})):
            if num_iters > 10 * n_pairs:
                LOGGER.warn("too many non-match iterations", extra={"n_pairs": n_pairs})
                return
            if num_pairs >= n_pairs:
                # end case, we have enough pairs
                return

            num_iters += 1
            seen: tuple[int, int] = tuple(sorted((pair_1[0], pair_2[0])))

            if pair_1[1] is None or pair_2[1] is None:
                continue  # no person
            if pair_1[1] == pair_2[1]:
                continue  # same person
            if seen in already_seen:
                continue  # already seen

            already_seen.add(seen)
            num_pairs += 1
            yield (pair_1[2], pair_2[2]), found_size

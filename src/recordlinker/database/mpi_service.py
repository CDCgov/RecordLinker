"""
recordlinker.linking.mpi_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides the data access functions to the MPI tables
"""

import typing
import uuid

from sqlalchemy import insert
from sqlalchemy import literal
from sqlalchemy import orm
from sqlalchemy import select
from sqlalchemy.sql import expression

from recordlinker import models
from recordlinker import schemas


def _filter_incorrect_blocks(
        record: schemas.PIIRecord,
        patients: typing.Sequence[models.Patient],
        blocking_keys: list[str]
) -> list[models.Patient]:
    """
    Filter a set of candidates returned via blocking from the MPI. The initial
    SQL query returns a collection of candidates comprised of all patients in
    the MPI belonging to a Person cluster for which at *least one* patient
    satisfied blocking criteria. This function filters that candidate set to
    include *only* those patients who either satisfied blocking criteria or
    were missing a value for one or more blocked fields. This eliminates 
    patients from consideration who have mismatched blocking information but
    belonged to a Person cluster where a different record had correct blocking
    values.

    :param record: The PIIRecord of the incoming patient.
    :param patients: The initial collection of candidates retrieved from the MPI.
    :param blocking_keys: A list of strings of the fields used for blocking.
    :returns: A filtered list of Patients from the MPI.
    """
    # Extract the acceptable blocking values from the incoming record
    # Keys have already been getattr validated by caller, no need
    # to check that they exist
    blocking_vals_in_incoming = {}
    for bk in blocking_keys:
        key = getattr(models.BlockingKey, bk)
        vals_blocked_from_key = [v for v in record.blocking_keys(key)]
        if len(vals_blocked_from_key) > 0:
            blocking_vals_in_incoming[bk] = vals_blocked_from_key

    # Can't modify sequence in place, so we'll build up a list of list idxs
    # to exclude for mpi patients who don't match blocking criteria exactly
    pats_to_exclude = set()
    for p in patients:
        # Note: This implementation searches for compatible values in the
        # fields of candidates. It is possible to write this inner loop
        # checking for incompatible values instead. This changes which loop
        # gets short-circuited. Performance testing found compatible search
        # faster than incompatible search due to generator termination and
        # time-complexity growth with number of blocking keys. The more
        # normalization and preprocessing done in `feature_iter`, the slower
        # this search method becomes. If heavy processing is performed,
        # consider switching to incompatible search.
        num_agreeing_blocking_fields = 0
        mpi_record = p.record
        for bk, allowed_vals in blocking_vals_in_incoming.items():
            # Compare incoming blocking value to what would be the blocking
            # value of the mpi record to make sure we compare on e.g. same
            # number of characters at beginning/end of string
            mpi_vals = mpi_record.blocking_keys(getattr(models.BlockingKey, bk))

            # Generator gets us best performance, fastest way to check membership
            # because we return True as soon as we get 1 rather than build the
            # whole list. Also count compatibility if mpi_val is missing.
            found_compatible_val = (len(mpi_vals) == 0) or any(x in mpi_vals for x in allowed_vals)
            if found_compatible_val:
                num_agreeing_blocking_fields += 1

        # If we get through all the blocking criteria with no missing entries
        # and no true-value agreement, we exclude
        if num_agreeing_blocking_fields < len(blocking_keys):
            pats_to_exclude.add(p.id)
    
    return [pat for pat in patients if pat.id not in pats_to_exclude]


def get_block_data(
    session: orm.Session, record: schemas.PIIRecord, algorithm_pass: models.AlgorithmPass
) -> typing.Sequence[models.Patient]:
    """
    Get all of the matching Patients for the given data using the provided
    blocking keys defined in the algorithm_pass. Also, get all the
    remaining Patient records in the Person clusters identified in
    blocking to calculate Belongingness Ratio.
    """
    # Create the base query
    base = expression.select(models.Patient.person_id).distinct()

    # Build the join criteria, we are joining the Blocking Value table
    # multiple times, once for each Blocking Key.  If a Patient record
    # has a matching Blocking Value for all the Blocking Keys, then it
    # is considered a match.
    for idx, key_id in enumerate(algorithm_pass.blocking_keys):
        # get the BlockingKey obj from the id
        if not hasattr(models.BlockingKey, key_id):
            raise ValueError(f"No BlockingKey with id {id} found.")
        key = getattr(models.BlockingKey, key_id)

        # Get all the possible values from the data for this key
        vals = [v for v in record.blocking_keys(key)]
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
                alias.value.in_(vals),
            ),
        )

    # Using the subquery of unique Patient IDs, select all the Patients
    expr = expression.select(models.Patient).where(models.Patient.person_id.in_(base))
    candidates = session.execute(expr).scalars().all()
    return _filter_incorrect_blocks(record, candidates, algorithm_pass.blocking_keys)


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

    patient = models.Patient(person=person, record=record, external_patient_id=external_patient_id)

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
            "_data": record.to_dict(prune_empty=True),
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
        patient.record = record
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
        record = records[idx] if records else patient.record
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
    query = (
        select(models.Person)
        .outerjoin(models.Patient, models.Patient.person_id == models.Person.id)
        .filter(models.Patient.id.is_(None))
        .order_by(models.Person.id)
    )
    if cursor:
        query = query.filter(models.Person.id > cursor)

    query = query.limit(
        limit
    )  # limit applied after cursor to ensure the limit is applied after the JOIN and starts from the cursor after the join

    return session.execute(query).scalars().all()

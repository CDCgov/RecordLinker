"""
recordlinker.linking.mpi_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides the data access functions to the MPI tables
"""

import typing
import uuid

from sqlalchemy import insert
from sqlalchemy import orm
from sqlalchemy import select
from sqlalchemy.sql import expression

from recordlinker import models
from recordlinker import schemas


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
    return session.execute(expr).scalars().all()


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
    # create a new Person record if one isn't provided
    person = person or models.Person()

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

    person = person or models.Person()
    session.add(person)
    session.flush()
    pat_data = [
        {
            "person_id": person.id,
            "_data": record.to_json(prune_empty=True),
            "external_patient_id": record.external_id,
            "external_person_id": external_person_id,
            "external_person_source": "IRIS" if external_person_id else None,
        }
        for record in records
    ]

    patients: list[models.Patient] = session.scalars(
        insert(models.Patient).returning(models.Patient, sort_by_parameter_order=True), pat_data
    ).all()

    insert_blocking_values(session, patients, records=records, commit=False)

    if commit:
        session.commit()
    return patients


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


def get_patient_by_reference_id(
    session: orm.Session, reference_id: uuid.UUID
) -> models.Patient | None:
    """
    Retrieve the Patient by their reference id
    """
    query = select(models.Patient).where(models.Patient.reference_id == reference_id)
    return session.scalar(query)


def get_person_by_reference_id(
    session: orm.Session, reference_id: uuid.UUID
) -> models.Person | None:
    """
    Retrieve the Person by their reference id
    """
    query = select(models.Person).where(models.Person.reference_id == reference_id)
    return session.scalar(query)


def update_person_cluster(
    session: orm.Session,
    patient: models.Patient,
    person: models.Person | None = None,
    commit: bool = True,
) -> models.Person:
    """
    Update the cluster for a given patient.
    """
    patient.person = person or models.Person()
    session.flush()

    if commit:
        session.commit()
    return patient.person


def reset_mpi(session: orm.Session, commit: bool = True):
    """
    Reset the MPI database by deleting all Person and Patient records.
    """
    session.query(models.BlockingValue).delete()
    session.query(models.Patient).delete()
    session.query(models.Person).delete()
    if commit:
        session.commit()

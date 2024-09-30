"""
recordlinker.linking.mpi_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides the data access functions to the MPI tables
"""

import typing

from sqlalchemy import orm
from sqlalchemy.sql import expression

from recordlinker import models


def get_block_data(
    session: orm.Session, record: models.PIIRecord, algo_config: dict
) -> list[models.Patient]:
    """
    Get all of the matching Patients for the given data using the provided
    blocking keys defined in the algo_config.
    """
    # Create the base query
    query = session.query(models.Patient)

    # Build the join criteria, we are joining the Blocking Value table
    # multiple times, once for each Blocking Key.  If a Patient record
    # has a matching Blocking Value for all the Blocking Keys, then it
    # is considered a match.
    for idx, block in enumerate(algo_config["blocks"]):
        key_name = block["value"].upper()
        if not hasattr(models.BlockingKey, key_name):
            raise ValueError(f"Invalid Blocking Key: {block}")
        # Get the matching Blocking Key based on the value in the algo_config
        key = models.BlockingKey[key_name]
        # Get all the possible values from the data for this key
        vals = [v for v in key.to_value(record)]
        # Create a dynamic alias for the Blocking Value table using the index
        # this is necessary since we are potentially joining the same table
        # multiple times with different conditions
        alias = orm.aliased(models.BlockingValue, name=f"bv{idx}")
        # Add a join clause to the mpi_blocking_value table for each Blocking Key.
        # This results in multiple joins to the same table, one for each Key, but
        # with different joining conditions.
        query = query.join(
            alias,
            expression.and_(
                models.Patient.id == alias.patient_id,
                alias.blockingkey == key.id,
                alias.value.in_(vals),
            ),
        )
    return query.all()


def insert_patient(
    session: orm.Session,
    record: models.PIIRecord,
    person: typing.Optional[models.Person] = None,
    external_patient_id: typing.Optional[str] = None,
    external_person_id: typing.Optional[str] = None,
    commit: bool = True,
) -> models.Patient:
    """
    Insert a new patient record into the database.
    """
    # create a new Person record if one isn't provided
    person = person or models.Person()

    patient = models.Patient(person=person, record=record, external_patient_id=external_patient_id)

    if external_person_id is not None:
        patient.external_person_id = external_person_id
        patient.external_person_source = "IRIS"

    # create a new Patient record
    session.add(patient)

    # insert blocking keys
    insert_blocking_keys(session, patient, commit=False)

    if commit:
        session.commit()
    return patient


def insert_blocking_keys(
    session: orm.Session,
    patient: models.Patient,
    commit: bool = True,
) -> list[models.BlockingValue]:
    """
    Inserts blocking keys for a patient record into the MPI database.
    """
    values: list[models.BlockingValue] = []
    # Iterate over all the Blocking Keys
    for key in models.BlockingKey:
        # For each Key, get all the values from the data dictionary
        # Many Keys will only have 1 value, but its possible that
        # a PII data dict could have multiple given names
        for val in key.to_value(patient.record):
            values.append(
                models.BlockingValue(patient=patient, blockingkey=key.id, value=val)
            )
    session.add_all(values)

    if commit:
        session.commit()
    return values

def get_all_algorithms(session: orm.Session) -> list[str]:
    """
    Gets a list of algorithms from the MPI database.
    returns: list of all labels column from algorithms table
    """

    algorithmsList = session.query(models.Algorithm.label).all()

    return [algorithm[0] for algorithm in algorithmsList]

def get_algorithm_by_label(session: orm.Session, label: str) -> models.Algorithm | None:
    """
    Gets a single algorithm by searching for the unique label
    returns: algorithm json string
    """

    if not label:
        algorithm = session.query(models.Algorithm).filter(models.Algorithm.is_default == True).first() # noqa: E712
    else:
        algorithm = session.query(models.Algorithm).filter(models.Algorithm.label == label).first()
  
    return algorithm
    
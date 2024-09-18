"""
recordlinker.linkage.simple_mpi
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides the data access functions to the MPI tables
"""

import typing

from sqlalchemy import orm
from sqlalchemy.sql import expression

from recordlinker.linkage import models


def get_block_data(
    session: orm.Session, data: dict, algo_config: dict
) -> list[models.Patient]:
    """
    Get all of the matching Patients for the given data using the provided
    blocking keys defined in the algo_config.
    """
    # Create the base query
    query = session.query(models.Patient)

    # Build the join criteria
    for block in algo_config["blocks"]:
        key_name = block["value"].upper()
        # Get the matching Blocking Key based on the value in the algo_config
        assert hasattr(models.BlockingKey, key_name), f"Invalid Blocking Key: {block}"
        key = models.BlockingKey[key_name]
        # Get all the possible values from the data for this key
        vals = [v for v in key.to_value(data)]
        # Add a join clause to the mpi_blocking_value table for each Blocking Key.
        # This results in multiple joins to the same table, one for each Key, but
        # with different joining conditions.
        query = query.join(
            models.BlockingValue,
            expression.and_(
                models.Patient.id == models.BlockingValue.patient_id,
                models.BlockingValue.blockingkey == key.id,
                models.BlockingValue.value.in_(vals),
            ),
        )

    return query.all()


def insert_matched_patient(
    session: orm.Session,
    data: dict,
    person_id: typing.Optional[int],
    external_person_id: typing.Optional[str],
    commit: bool = True,
) -> models.Patient:
    """
    Insert a new patient record into the database.
    """
    if person_id is None:
        # create a new Person record
        person = models.Person()
        session.add(person)
        # flush the session to get the person_id
        session.flush()
        person_id = person.id

    if external_person_id is not None:
        # create a new ExternalPerson record if it doesn't exist
        external_person = models.ExternalPerson(
            person_id=person_id,
            external_id=external_person_id,
            source="IRIS",
        )
        session.merge(external_person)

    # create a new Patient record
    patient = models.Patient(person_id=person_id, data=data)
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
        for val in key.to_value(patient.data):
            values.append(
                models.BlockingValue(
                    patient_id=patient.id, blockingkey=key.id, value=val
                )
            )
    session.add_all(values)

    if commit:
        session.commit()
    return values

"""
recordlinker.routes.person_router
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the person router for the RecordLinker API. Exposing
the person API endpoints.
"""

import typing
import uuid

import fastapi
import sqlalchemy.orm as orm

from recordlinker import models
from recordlinker import schemas
from recordlinker.database import get_session
from recordlinker.database import mpi_service as service

router = fastapi.APIRouter()


def patients_by_id_or_422(
    session: orm.Session, reference_ids: typing.Sequence[uuid.UUID]
) -> typing.Sequence[models.Patient]:
    """
    Retrieve the Patients by their reference ids or raise a 422 error response.
    """
    patients = service.get_patients_by_reference_ids(session, *reference_ids)
    if None in patients:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "loc": ["body", "patients"],
                    "msg": "Invalid patient reference id",
                    "type": "value_error",
                }
            ],
        )
    return patients  # type: ignore


def patients_by_person_id_or_422(
    session: orm.Session, person_ids: typing.Sequence[int]
) -> typing.Sequence[models.Patient]:
    """
    Retrieve the Patients by their person id(s) or raise a 422 error response.
    """
    patients = service.get_patients_by_person_ids(session, person_ids)
    if not patients:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "loc": ["body", "patients"],
                    "msg": "Invalid person_id(s). No patients found for any of the provided person_id(s)",
                    "type": "value_error",
                }
            ],
        )
    return patients  # type: ignore


@router.post(
    "",
    summary="Create a new Person cluster",
    status_code=fastapi.status.HTTP_201_CREATED,
)
def create_person(
    data: typing.Annotated[schemas.PatientRefs, fastapi.Body()],
    session: orm.Session = fastapi.Depends(get_session),
) -> schemas.PersonRef:
    """
    Create a new Person in the MPI database and link the Patients to them.
    """
    patients = patients_by_id_or_422(session, data.patients)

    person = service.update_person_cluster(session, patients, commit=False)
    return schemas.PersonRef(person_reference_id=person.reference_id)


@router.patch(
    "/{person_reference_id}",
    summary="Assign Patients to existing Person",
    status_code=fastapi.status.HTTP_200_OK,
)
def update_person(
    person_reference_id: uuid.UUID,
    data: typing.Annotated[schemas.PatientRefs, fastapi.Body()],
    session: orm.Session = fastapi.Depends(get_session),
) -> schemas.PersonRef:
    """
    Assign the Patients to an existing Person cluster.
    """
    person = service.get_person_by_reference_id(session, person_reference_id)
    if person is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)
    patients = patients_by_id_or_422(session, data.patients)

    person = service.update_person_cluster(session, patients, person, commit=False)
    return schemas.PersonRef(person_reference_id=person.reference_id)


@router.post(
    "/{person_reference_id}/merge",
    summary="Merge Person clusters",
    status_code=fastapi.status.HTTP_200_OK,
)
def merge_person_clusters(
    person_reference_id: uuid.UUID,
    data: typing.Annotated[schemas.PersonRefs, fastapi.Body()],
    session: orm.Session = fastapi.Depends(get_session),
) -> schemas.PersonRef:
    """
    Merges Person cluster(s) into the Person cluster referenced by `person_reference_id`.
    """
    # Get the person_reference_id the person clusters will be merged into
    person = service.get_person_by_reference_id(session, person_reference_id)

    if person is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)

    # Get all persons by person_reference_id that will be merged
    persons = service.get_persons_by_reference_ids(session, data.person_reference_ids)
    person_ids = [person.id for person in persons]

    # Get all of the patients from the person clusters to be merged
    patients = patients_by_person_id_or_422(session, person_ids)

    # Merge the person clusters
    person = service.update_person_cluster(session, patients, person, commit=False)

    # Should we clean up orphaned person clusters after merging?

    return schemas.PersonRef(person_reference_id=person.reference_id)

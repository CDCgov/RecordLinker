"""
recordlinker.routes.person_router
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the person router for the RecordLinker API. Exposing
the person API endpoints.
"""

import typing
import uuid

import fastapi
import pydantic
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


def persons_by_reference_id_or_422(
    session: orm.Session, person_reference_ids: typing.Sequence[uuid.UUID]
) -> typing.Sequence[models.Patient]:
    """
    Retrieve the Patients by their reference ids or raise a 422 error response.
    """
    persons = service.get_persons_by_reference_ids(session, *person_reference_ids)
    if None in persons:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "loc": ["body", "person_reference_ids"],
                    "msg": "Invalid person reference id",
                    "type": "value_error",
                }
            ],
        )
    return persons  # type: ignore


@router.post(
    "",
    summary="Create a new Person cluster",
    status_code=fastapi.status.HTTP_201_CREATED,
    name="create-person",
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
    name="update-person",
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


@router.get(
    "/orphaned",
    summary="Retrieve orphaned persons",
    status_code=fastapi.status.HTTP_200_OK,
    name="get-orphaned-persons",
)
def get_orphaned_persons(
    request: fastapi.Request,
    session: orm.Session = fastapi.Depends(get_session),
    limit: int | None = fastapi.Query(50, alias="limit", ge=1, le=1000),
    cursor: uuid.UUID | None = fastapi.Query(None, alias="cursor"),
) -> schemas.PaginatedRefs:
    """
    Retrieve person_reference_id(s) for all Persons that are not linked to any Patients.
    """
    # Check if the cursor is a valid Person reference_id
    if cursor:
        person = service.get_persons_by_reference_ids(session, cursor)
        if not person or person[0] is None:
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=[
                    {
                        "loc": ["query", "cursor"],
                        "msg": "Cursor is an invalid Person reference_id",
                        "type": "value_error",
                    }
                ],
            )
        # Replace the cursor with the Patient id instead of reference_id
        cur = person[0].id
    else:
        cur = None

    persons = service.get_orphaned_persons(session, limit, cur)
    if not persons:
        return schemas.PaginatedRefs(
            data=[], meta=schemas.PaginatedMetaData(next_cursor=None, next=None)
        )

    # Prepare the meta data
    next_cursor: uuid.UUID | None = persons[-1].reference_id if len(persons) == limit else None
    next_url: str | None = str(request.url.include_query_params(cursor=next_cursor)) if next_cursor else None

    return schemas.PaginatedRefs(
        data=[p.reference_id for p in persons if p.reference_id],
        meta=schemas.PaginatedMetaData(
            next_cursor=next_cursor,
            next=pydantic.HttpUrl(next_url) if next_url else None,
        ),
    )


@router.get(
    "/{person_reference_id}",
    summary="Retrieve a person cluster",
    status_code=fastapi.status.HTTP_200_OK,
    name="get-person",
)
def get_person(
    person_reference_id: uuid.UUID,
    session: orm.Session = fastapi.Depends(get_session),
) -> schemas.PersonInfo:
    """
    Retrieve an existing person cluster in the MPI
    """
    person = service.get_person_by_reference_id(session, person_reference_id)
    if person is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)

    return schemas.PersonInfo(
        person_reference_id=person.reference_id,
        patient_reference_ids=[patient.reference_id for patient in person.patients],
    )


@router.post(
    "/{merge_into_id}/merge",
    summary="Merge Person clusters",
    status_code=fastapi.status.HTTP_200_OK,
    name="merge-person-clusters",
)
def merge_person_clusters(
    merge_into_id: uuid.UUID,
    data: typing.Annotated[schemas.PersonRefs, fastapi.Body()],
    delete_person_clusters: bool = False,
    session: orm.Session = fastapi.Depends(get_session),
) -> schemas.PersonRef:
    """
    Merges Person cluster(s) into the Person cluster referenced by `merge_into_id`. Optionally
    delete the merged Person clusters.
    """
    # Check that the merge_into_id is not in the list of person_reference_ids
    if merge_into_id in data.person_reference_ids:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "loc": ["body", "person_reference_ids"],
                    "msg": "The merge_into_id cannot be in the person_reference_ids.",
                    "type": "value_error",
                }
            ],
        )

    # Get the person that the person clusters will be merged into
    per = service.get_person_by_reference_id(session, merge_into_id)

    if per is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)

    # Get all persons by person_reference_id that will be merged
    persons = persons_by_reference_id_or_422(session, data.person_reference_ids)
    person_ids = [person.id for person in persons]

    # Update all of the patients from the person clusters to be merged
    person = service.update_patient_person_ids(session, per, person_ids, commit=False)

    # Clean up orphaned person clusters
    if delete_person_clusters:
        service.delete_persons(session, persons, commit=False)

    return schemas.PersonRef(person_reference_id=person.reference_id)


@router.delete(
    "/{person_reference_id}",
    summary="Delete an empty Person",
    status_code=fastapi.status.HTTP_204_NO_CONTENT,
    name="delete-empty-person",
    responses={
        404: {"description": "Not Found", "model": schemas.ErrorResponse},
        403: {
            "description": "Forbidden",
            "model": schemas.ErrorResponse,
        },
    },
)
def delete_empty_person(
    person_reference_id: uuid.UUID,
    session: orm.Session = fastapi.Depends(get_session),
    name="delete-empty-person",
):
    """
    Delete an empty Person from the MPI database.
    """
    # Check that person_reference_id is valid
    person = service.get_person_by_reference_id(session, person_reference_id)

    if person is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=[
                {
                    "loc": ["path", "person_reference_id"],
                    "msg": "Person not found",
                    "type": "not_found",
                }
            ],
        )

    # Check if the person has associated patients
    has_patients = service.check_person_for_patients(session, person)
    if has_patients:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_403_FORBIDDEN,
            detail=[
                {
                    "loc": ["path", "person_reference_id"],
                    "msg": "Cannot delete Person because the ID has associated Patients.",
                    "type": "value_error",
                }
            ],
        )

    # Delete the person
    service.delete_persons(session, [person])
    return fastapi.Response(status_code=fastapi.status.HTTP_204_NO_CONTENT)

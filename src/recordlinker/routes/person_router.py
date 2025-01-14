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

from recordlinker import schemas
from recordlinker.database import get_session
from recordlinker.database import mpi_service as service

router = fastapi.APIRouter()


@router.post(
    "",
    summary="Create a new Person cluster",
    status_code=fastapi.status.HTTP_201_CREATED,
)
def create_person(
    data: typing.Annotated[schemas.PersonInput, fastapi.Body()],
    session: orm.Session = fastapi.Depends(get_session)
) -> schemas.PersonRef:
    """
    Create a new Person in the MPI database and link the Patients to them.
    """
    patients: list[models.Patient] = []
    for ref_id in data.patients_reference_ids:
        patient = service.get_patient_by_reference_id(session, ref_id)
        if patient is None:
            raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)
        patients.append(patient)
    patient = service.get_patient_by_reference_id(session, patient_reference_id)
    if patient is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)

    person = service.update_person_cluster(session, patients, commit=False)
    return schemas.PatientPersonRef(
        patient_reference_id=patient.reference_id, person_reference_id=person.reference_id
    )


@router.patch(
    "/{patient_reference_id}/person",
    summary="Assign Patient to existing Person",
    status_code=fastapi.status.HTTP_200_OK,
    deprecated=True,
)
def update_person(
    patient_reference_id: uuid.UUID,
    data: schemas.PersonRef,
    session: orm.Session = fastapi.Depends(get_session),
) -> schemas.PatientPersonRef:
    """
    **NOTE**: This endpoint is deprecated. Use the PATCH `/person/{person_reference_id}` endpoint instead.

    **NOTE**: This endpoint will be removed in v25.2.0.

    Update the Person linked on the Patient.
    """
    patient = service.get_patient_by_reference_id(session, patient_reference_id)
    if patient is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)

    person = service.get_person_by_reference_id(session, data.person_reference_id)
    if person is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY)

    person = service.update_person_cluster(session, patient, person, commit=False)
    return schemas.PatientPersonRef(
        patient_reference_id=patient.reference_id, person_reference_id=person.reference_id
    )

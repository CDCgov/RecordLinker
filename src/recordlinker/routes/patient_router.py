"""
recordlinker.routes.patient_router
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the patient router for the RecordLinker API. Exposing
the patient API endpoints.
"""

import uuid

import fastapi
import sqlalchemy.orm as orm

from recordlinker import schemas
from recordlinker.database import get_session
from recordlinker.database import mpi_service as service

router = fastapi.APIRouter()


@router.post(
    "/{patient_reference_id}/person",
    summary="Assign Patient to new Person",
    status_code=fastapi.status.HTTP_201_CREATED,
    deprecated=True,
)
def create_person(
    patient_reference_id: uuid.UUID, session: orm.Session = fastapi.Depends(get_session)
) -> schemas.PatientPersonRef:
    """
    **NOTE**: This endpoint is deprecated. Use the POST `/person` endpoint instead.

    **NOTE**: This endpoint will be removed in v25.2.0.

    Create a new Person in the MPI database and link the Patient to them.
    """
    patient = service.get_patients_by_reference_ids(session, patient_reference_id)[0]
    if patient is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)

    person = service.update_person_cluster(session, [patient], commit=False)
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
    patient = service.get_patients_by_reference_ids(session, patient_reference_id)[0]
    if patient is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)

    person = service.get_person_by_reference_id(session, data.person_reference_id)
    if person is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY)

    person = service.update_person_cluster(session, [patient], person, commit=False)
    return schemas.PatientPersonRef(
        patient_reference_id=patient.reference_id, person_reference_id=person.reference_id
    )

@router.delete(
    "/{patient_reference_id}",
    summary="Delete a Patient",
    status_code=fastapi.status.HTTP_204_NO_CONTENT,
)
def delete_patient(
    patient_reference_id: uuid.UUID, session: orm.Session = fastapi.Depends(get_session)
) -> None:
    """
    Delete a Patient from the mpi database.
    """
    patient = service.get_patients_by_reference_ids(session, patient_reference_id)[0]

    if patient is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)
    
    return service.delete_patient(session, patient)

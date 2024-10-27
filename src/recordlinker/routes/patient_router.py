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
from recordlinker.linking import mpi_service as service

router = fastapi.APIRouter()


@router.post(
    "/{patient_ref_id}/person",
    summary="Assign Patient to new Person",
    status_code=fastapi.status.HTTP_201_CREATED,
)
def create_person(
    patient_ref_id: uuid.UUID, session: orm.Session = fastapi.Depends(get_session)
) -> schemas.PatientPersonRef:
    """
    Create a new Person in the MPI database and link the Patient to them.
    """
    patient = service.get_patient_by_reference_id(session, patient_ref_id)
    if patient is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)

    person = service.update_person_cluster(session, patient, commit=False)
    return schemas.PatientPersonRef(
        patient_ref_id=patient.reference_id, person_ref_id=person.reference_id
    )


@router.patch(
    "/{patient_ref_id}/person",
    summary="Assign Patient to existing Person",
    status_code=fastapi.status.HTTP_200_OK,
)
def update_person(
    patient_ref_id: uuid.UUID,
    data: schemas.PersonRef,
    session: orm.Session = fastapi.Depends(get_session),
) -> schemas.PatientPersonRef:
    """
    Update the Person linked on the Patient.
    """
    patient = service.get_patient_by_reference_id(session, patient_ref_id)
    if patient is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)

    person = service.get_person_by_reference_id(session, data.person_ref_id)
    if person is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_400_BAD_REQUEST)

    person = service.update_person_cluster(session, patient, person, commit=False)
    return schemas.PatientPersonRef(
        patient_ref_id=patient.reference_id, person_ref_id=person.reference_id
    )

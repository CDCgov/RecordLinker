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
)
def create_person(
    patient_reference_id: uuid.UUID, session: orm.Session = fastapi.Depends(get_session)
) -> schemas.PatientPersonRef:
    """
    Create a new Person in the MPI database and link the Patient to them.
    """
    patient = service.get_patient_by_reference_id(session, patient_reference_id)
    if patient is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)

    person = service.update_person_cluster(session, patient, commit=False)
    return schemas.PatientPersonRef(
        patient_reference_id=patient.reference_id, person_reference_id=person.reference_id
    )


@router.patch(
    "/{patient_reference_id}/person",
    summary="Assign Patient to existing Person",
    status_code=fastapi.status.HTTP_200_OK,
)
def update_person(
    patient_reference_id: uuid.UUID,
    data: schemas.PersonRef,
    session: orm.Session = fastapi.Depends(get_session),
) -> schemas.PatientPersonRef:
    """
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
    patient = service.get_patient_by_reference_id(session, patient_reference_id)

    if patient is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)
    
    return service.delete_patient(session, patient)

@router.post(
    "/person/{person_reference_id}",
    summary="Create a patient record and link to an existing person",
    status_code=fastapi.status.HTTP_201_CREATED,
)
def create_patient(
    person_reference_id: uuid.UUID, record: schemas.PIIRecord, session: orm.Session = fastapi.Depends(get_session)
) -> schemas.PatientRef:
    """
    Create a new patient record in the mpi
    """
    person = service.get_person_by_reference_id(session, person_reference_id)

    if person is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)
    
    print("made it here")
    patient = service.insert_patient(session, record, person)
    return schemas.PatientRef(reference_id=patient.reference_id)


@router.patch(
    "/{patient_reference_id}",
    summary="Update a patient record",
    status_code=fastapi.status.HTTP_200_OK,
)
def update_patient(
    patient_reference_id: uuid.UUID, record: schemas.PIIRecord, session: orm.Session = fastapi.Depends(get_session)
) -> schemas.PatientRef:
    """
    Update an existing patient record in the mpi
    """
    patient = service.get_patient_by_reference_id(session, patient_reference_id)
    if patient is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)
    
    #update the patient record with the new data

    #return a reference object to the updated patient
"""
recordlinker.routes.patient_router
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the patient router for the RecordLinker API. Exposing
the patient API endpoints.
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

    **NOTE**: This endpoint will be removed in v25.3.0.

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

    **NOTE**: This endpoint will be removed in v25.3.0.

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


@router.post(
    "/",
    summary="Create a patient record and link to an existing person",
    status_code=fastapi.status.HTTP_201_CREATED,
)
def create_patient(
    payload: typing.Annotated[schemas.PatientCreatePayload, fastapi.Body],
    session: orm.Session = fastapi.Depends(get_session),
) -> schemas.PatientRef:
    """
    Create a new patient record in the MPI and link to an existing person.
    """
    person = service.get_person_by_reference_id(session, payload.person_reference_id)

    if person is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "loc": ["body", "person_reference_id"],
                    "msg": "Person not found",
                    "type": "value_error",
                }
            ],
        )

    patient = service.insert_patient(
        session,
        payload.record,
        person=person,
        external_patient_id=payload.record.external_id,
        commit=False,
    )
    return schemas.PatientRef(
        patient_reference_id=patient.reference_id, external_patient_id=patient.external_patient_id
    )


@router.get(
    "/{patient_reference_id}",
    summary="Retrieve a patient record",
    status_code=fastapi.status.HTTP_200_OK,
)
def get_patient(
    patient_reference_id: uuid.UUID,
    session: orm.Session = fastapi.Depends(get_session),
) -> schemas.PatientInfo:
    """
    Retrieve an existing patient record in the MPI
    """
    patient = service.get_patients_by_reference_ids(session, patient_reference_id)[0]
    if patient is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)

    return schemas.PatientInfo(
        patient_reference_id=patient.reference_id,
        person_reference_id=patient.person.reference_id,
        record=patient.record,
        external_patient_id=patient.external_patient_id,
        external_person_id=patient.external_person_id)


@router.patch(
    "/{patient_reference_id}",
    summary="Update a patient record",
    status_code=fastapi.status.HTTP_200_OK,
)
def update_patient(
    patient_reference_id: uuid.UUID,
    payload: typing.Annotated[schemas.PatientUpdatePayload, fastapi.Body],
    session: orm.Session = fastapi.Depends(get_session),
) -> schemas.PatientRef:
    """
    Update an existing patient record in the MPI
    """
    patient = service.get_patients_by_reference_ids(session, patient_reference_id)[0]
    if patient is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)

    person = None
    if payload.person_reference_id:
        person = service.get_person_by_reference_id(session, payload.person_reference_id)
        if person is None:
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=[
                    {
                        "loc": ["body", "person_reference_id"],
                        "msg": "Person not found",
                        "type": "value_error",
                    }
                ],
            )

    external_patient_id = getattr(payload.record, "external_id", None)
    patient = service.update_patient(
        session,
        patient,
        person=person,
        record=payload.record,
        external_patient_id=external_patient_id,
        commit=False,
    )
    return schemas.PatientRef(
        patient_reference_id=patient.reference_id, external_patient_id=patient.external_patient_id
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

"""
recordlinker.routes.patient_router
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the patient router for the RecordLinker API. Exposing
the patient API endpoints.
"""

import typing
import uuid

import fastapi
import pydantic
import sqlalchemy.orm as orm

from recordlinker import schemas
from recordlinker.database import get_session
from recordlinker.database import mpi_service as service

router = fastapi.APIRouter()


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
    "/orphaned", summary="Retrieve orphaned patients", status_code=fastapi.status.HTTP_200_OK
)
def get_orphaned_patients(
    request: fastapi.Request,
    session: orm.Session = fastapi.Depends(get_session),
    limit: int | None = fastapi.Query(50, alias="limit", ge=1, le=1000),
    cursor: uuid.UUID | None = fastapi.Query(None, alias="cursor"),
) -> schemas.PaginatedRefs:
    """
    Retrieve patient_reference_id(s) for all Patients that are not linked to a Person.
    """
    # Check if the cursor is a valid Patient reference_id
    if cursor:
        patient = service.get_patients_by_reference_ids(session, cursor)
        if not patient or patient[0] is None:
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=[
                    {
                        "loc": ["query", "cursor"],
                        "msg": "Cursor is an invalid Patient reference_id",
                        "type": "value_error",
                    }
                ],
            )
        # Replace the cursor with the Patient id instead of reference_id
        cur = patient[0].id
    else:
        cur = None

    patients = service.get_orphaned_patients(session, limit, cur)
    if not patients:
        return schemas.PaginatedRefs(
            data=[], meta=schemas.PaginatedMetaData(next_cursor=None, next=None)
        )
    # Prepare the meta data
    next_cursor = patients[-1].reference_id if len(patients) == limit else None
    next_url = (
        f"{request.base_url}patient/orphaned?limit={limit}&cursor={next_cursor}"
        if next_cursor
        else None
    )

    return schemas.PaginatedRefs(
        data=[p.reference_id for p in patients if p.reference_id],
        meta=schemas.PaginatedMetaData(
            next_cursor=next_cursor,
            next=pydantic.HttpUrl(next_url) if next_url else None,
        ),
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
        record=schemas.PIIRecord.from_patient(patient),
        external_patient_id=patient.external_patient_id,
        external_person_id=patient.external_person_id,
    )


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

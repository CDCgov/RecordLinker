"""
recordlinker.routes.link_router
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the link router for the RecordLinker API. Exposing
API endpoints to link patient records.
"""

import typing

import fastapi
import sqlalchemy.orm as orm

from recordlinker import models
from recordlinker import schemas
from recordlinker.database import algorithm_service
from recordlinker.database import get_session
from recordlinker.hl7 import fhir
from recordlinker.linking import link

router = fastapi.APIRouter()


def algorithm_or_422(db_session: orm.Session, label: str | None) -> models.Algorithm:
    """
    Get the Algorithm, or default if no label. Raise a 422 if no Algorithm can be found.
    """
    algorithm = (
        algorithm_service.get_algorithm(db_session, label)
        if label
        else algorithm_service.default_algorithm(db_session)
    )
    if not algorithm:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No algorithm found",
        )
    return algorithm


@router.post("", summary="Link Record")
async def link_piirecord(
    request: fastapi.Request,
    input: typing.Annotated[schemas.LinkInput, fastapi.Body()],
    response: fastapi.Response,
    db_session: orm.Session = fastapi.Depends(get_session),
) -> schemas.LinkResponse:
    """
    Compare a PII Record with records in the Master Patient Index (MPI) to
    check for matches with existing patient records If matches are found,
    returns the patient and person reference id's
    """
    algorithm = algorithm_or_422(db_session, input.algorithm)

    (patient, person, results, prediction) = link.link_record_against_mpi(
        record=input.record,
        session=db_session,
        algorithm=algorithm,
        external_person_id=input.external_person_id,
    )
    return schemas.LinkResponse(
        prediction=prediction,
        patient_reference_id=patient.reference_id,
        person_reference_id=(person and person.reference_id),
        results=[schemas.LinkResult(**r.__dict__) for r in results],
    )


@router.post("/fhir", summary="Link FHIR")
async def link_fhir(
    request: fastapi.Request,
    input: typing.Annotated[schemas.LinkFhirInput, fastapi.Body()],
    response: fastapi.Response,
    db_session: orm.Session = fastapi.Depends(get_session),
) -> schemas.LinkFhirResponse:
    """
    Compare a FHIR bundle with records in the Master Patient Index (MPI) to
    check for matches with existing patient records If matches are found,
    returns the FHIR bundle with updated references to existing patients.
    """
    algorithm = algorithm_or_422(db_session, input.algorithm)

    # Now extract the patient record we want to link
    patient: dict = fhir.get_first_patient_resource(input.bundle)
    if not patient:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Supplied bundle contains no Patient resource",
        )
    try:
        record: schemas.PIIRecord = fhir.fhir_record_to_pii_record(patient)
    except ValueError:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid Patient resource",
        )

    (patient, person, results, prediction) = link.link_record_against_mpi(
        record=record,
        session=db_session,
        algorithm=algorithm,
        external_person_id=input.external_person_id,
    )
    return schemas.LinkFhirResponse(
        prediction=prediction,
        patient_reference_id=patient.reference_id,
        person_reference_id=(person and person.reference_id),
        results=[schemas.LinkResult(**r.__dict__) for r in results],
        updated_bundle=(
            person
            and fhir.add_person_resource(str(person.reference_id), record.external_id, input.bundle)
        ),
    )

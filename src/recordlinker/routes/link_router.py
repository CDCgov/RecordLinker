"""
recordlinker.routes.link_router
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the link router for the RecordLinker API. Exposing
API endpoints to link patient records.
"""

import typing

import fastapi
import sqlalchemy.orm as orm

from recordlinker import schemas
from recordlinker.database import algorithm_service
from recordlinker.database import get_session
from recordlinker.hl7 import fhir
from recordlinker.linking import link

router = fastapi.APIRouter()


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
    if input.algorithm:
        algorithm = algorithm_service.get_algorithm(db_session, input.algorithm)
    else:
        algorithm = algorithm_service.default_algorithm(db_session)

    if not algorithm:
        msg = "Error: No algorithm found"
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg
        )

    # link the record
    try:
        # Make a copy of record_to_link so we don't modify the original
        (patient, person, results) = link.link_record_against_mpi(
            record=input.record,
            session=db_session,
            algorithm=algorithm,
            external_person_id=input.external_person_id,
        )
        return schemas.LinkResponse(
            patient_reference_id=patient.reference_id,
            person_reference_id=person.reference_id,
            results=results
        )

    except ValueError:
        msg = "Error: Bad request"
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_400_BAD_REQUEST, detail=msg)


@router.post("/dibbs", summary="Link FHIR for DIBBs")
async def link_dibbs(
    request: fastapi.Request,
    input: typing.Annotated[schemas.LinkFhirInput, fastapi.Body()],
    response: fastapi.Response,
    db_session: orm.Session = fastapi.Depends(get_session),
) -> schemas.LinkFhirResponse:
    """
    Compare a FHIR bundle with records in the Master Patient Index (MPI) to
    check for matches with existing patient records If matches are found,
    returns the FHIR bundle with updated references to existing patients.
    This is a special endpoint that allows integration into a DIBBs pipeline,
    as it accepts and returns FHIR bundles.
    """
    input_bundle = input.bundle
    external_id = input.external_person_id

    if input.algorithm:
        algorithm = algorithm_service.get_algorithm(db_session, input.algorithm)
    else:
        algorithm = algorithm_service.default_algorithm(db_session)

    if not algorithm:
        response.status_code = fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY
        return schemas.LinkFhirResponse(
            found_match=False,
            updated_bundle=input_bundle,
            message="Error: No algorithm found",
        )

    # Now extract the patient record we want to link
    try:
        record_to_link = [
            entry.get("resource")
            for entry in input_bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType", "") == "Patient"
        ][0]
    except IndexError:
        response.status_code = fastapi.status.HTTP_400_BAD_REQUEST
        return schemas.LinkFhirResponse(
            found_match=False,
            updated_bundle=input_bundle,
            message="Supplied bundle contains no Patient resource to link on.",
        )

    # convert record to PII
    pii_record: schemas.PIIRecord = fhir.fhir_record_to_pii_record(record_to_link)

    # Now link the record
    try:
        (found_match, new_person_id, _) = link.link_record_against_mpi(
            record=pii_record,
            session=db_session,
            algorithm=algorithm,
            external_person_id=external_id,
        )
        updated_bundle = fhir.add_person_resource(
            str(new_person_id), pii_record.external_id, input_bundle
        )
        return schemas.LinkFhirResponse(found_match=found_match, updated_bundle=updated_bundle)

    except ValueError as err:
        response.status_code = fastapi.status.HTTP_400_BAD_REQUEST
        return schemas.LinkFhirResponse(
            found_match=False,
            updated_bundle=input_bundle,
            message=f"Could not connect to database: {err}",
        )


@router.post("/fhir", summary="Link FHIR")
async def link_fhir(
    request: fastapi.Request,
    input: typing.Annotated[schemas.LinkFhirInput, fastapi.Body()],
    response: fastapi.Response,
    db_session: orm.Session = fastapi.Depends(get_session),
) -> schemas.LinkResponse:
    """
    Compare a FHIR bundle with records in the Master Patient Index (MPI) to
    check for matches with existing patient records If matches are found,
    returns the patient and person reference id's
    """
    input_bundle = input.bundle
    external_id = input.external_person_id

    if input.algorithm:
        algorithm = algorithm_service.get_algorithm(db_session, input.algorithm)
    else:
        algorithm = algorithm_service.default_algorithm(db_session)

    if not algorithm:
        response.status_code = fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY
        raise fastapi.HTTPException(status_code=422, detail="Error: No algorithm found")

    # Now extract the patient record we want to link
    try:
        record_to_link = [
            entry.get("resource")
            for entry in input_bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType", "") == "Patient"
        ][0]
    except IndexError:
        response.status_code = fastapi.status.HTTP_400_BAD_REQUEST
        raise fastapi.HTTPException(
            status_code=400,
            detail="Error: Supplied bundle contains no Patient resource to link on.",
        )

    # convert record to PII
    pii_record: schemas.PIIRecord = fhir.fhir_record_to_pii_record(record_to_link)

    # link the record
    try:
        # Make a copy of pii_record so we don't modify the original
        (patient, person, results) = link.link_record_against_mpi(
            record=pii_record,
            session=db_session,
            algorithm=algorithm,
            external_person_id=external_id,
        )
        return schemas.LinkResponse(
            patient_reference_id=patient.reference_id,
            person_reference_id=person.reference_id,
            results=results
        )

    except ValueError:
        response.status_code = fastapi.status.HTTP_400_BAD_REQUEST
        raise fastapi.HTTPException(status_code=400, detail="Error: Bad request")

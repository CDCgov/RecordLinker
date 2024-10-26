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
from recordlinker import utils
from recordlinker.database import get_session
from recordlinker.linking import algorithm_service
from recordlinker.linking import link

router = fastapi.APIRouter()


# Sample requests and responses for docs
# TODO: These assets need to be installed with the python code
sample_link_record_requests = utils.read_json("assets", "sample_link_record_requests.json")
sample_link_record_responses = utils.read_json("assets", "sample_link_record_responses.json")


@router.post("")
async def link_piirecord(
    request: fastapi.Request,
    input: typing.Annotated[schemas.LinkInput, fastapi.Body()],
    response: fastapi.Response,
    db_session: orm.Session = fastapi.Depends(get_session),
) -> schemas.LinkResponse:
    """
    Compare a PII Reocrd with records in the Master Patient Index (MPI) to
    check for matches with existing patient records If matches are found,
    returns the patient and person reference id's
    """
    if input.algorithm:
        algorithm = algorithm_service.get_algorithm(db_session, input.algorithm)
    else:
        algorithm = algorithm_service.default_algorithm(db_session)

    if not algorithm:
        msg = "Error: Invalid algorithm specified"
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)

    # link the record
    try:
        # Make a copy of record_to_link so we don't modify the original
        (found_match, new_person_id, patient_reference_id) = link.link_record_against_mpi(
            record=input.record,
            session=db_session,
            algorithm=algorithm,
            external_person_id=input.external_person_id,
        )
        return schemas.LinkResponse(
            is_match=found_match,
            patient_reference_id=patient_reference_id,
            person_reference_id=new_person_id,
        )

    except ValueError:
        msg = "Error: Bad request"
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_400_BAD_REQUEST, detail=msg)


@router.post("/fhir", status_code=200, responses={200: sample_link_record_responses})
async def link_fhir(
    request: fastapi.Request,
    input: typing.Annotated[
        schemas.LinkFhirInput, fastapi.Body(examples=sample_link_record_requests)
    ],
    response: fastapi.Response,
    db_session: orm.Session = fastapi.Depends(get_session),
) -> schemas.LinkFhirResponse:
    """
    Compare a FHIR bundle with records in the Master Patient Index (MPI) to
    check for matches with existing patient records If matches are found,
    returns the bundle with updated references to existing patients.
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
            message="Error: Invalid algorithm specified",
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
    pii_record: schemas.PIIRecord = link.fhir_record_to_pii_record(record_to_link)

    # Now link the record
    try:
        (found_match, new_person_id, _) = link.link_record_against_mpi(
            record=pii_record,
            session=db_session,
            algorithm=algorithm,
            external_person_id=external_id,
        )
        updated_bundle = link.add_person_resource(
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

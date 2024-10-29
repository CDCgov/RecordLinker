import copy
import uuid
from pathlib import Path
from typing import Annotated
from typing import Optional

from fastapi import Body
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi import status
from pydantic import BaseModel
from pydantic import Field
from sqlalchemy import orm
from sqlalchemy.sql import expression

from recordlinker import middleware
from recordlinker import schemas
from recordlinker import utils
from recordlinker.base_service import BaseService
from recordlinker.database import get_session
from recordlinker.linking import algorithm_service
from recordlinker.linking import link
from recordlinker.routes.algorithm_router import router as algorithm_router
from recordlinker.routes.patient_router import router as patient_router

# Instantiate FastAPI via DIBBs' BaseService class
app = BaseService(
    service_name="DIBBs Record Linkage Service",
    service_path="/record-linkage",
    description_path=str(Path(__file__).parent.parent.parent / "README.md"),
    include_health_check_endpoint=False,
    # openapi_url="/record-linkage/openapi.json",
).start()
app.add_middleware(middleware.CorrelationIdMiddleware)
app.add_middleware(middleware.AccessLogMiddleware)
app.include_router(algorithm_router, prefix="/algorithm", tags=["algorithm"])
app.include_router(patient_router, prefix="/patient", tags=["patient"])


# Request and response models
class LinkRecordInput(BaseModel):
    """
    Schema for requests to the /link-record endpoint.
    """

    bundle: dict = Field(
        description="A FHIR bundle containing a patient resource to be checked "
        "for links to existing patient records"
    )
    algorithm: Optional[str] = Field(
        description="Optionally, a string that maps to an algorithm label stored in "
        "algorithm table",
        default=None,
    )
    external_person_id: Optional[str] = Field(
        description="The External Identifier, provided by the client,"
        " for a unique patient/person that is linked to patient(s)",
        default=None,
    )


class LinkRecordResponse(BaseModel):
    """
    The schema for responses from the /link-record endpoint.
    """

    found_match: bool = Field(
        description="A true value indicates that one or more existing records "
        "matched with the provided record, and these results have been linked."
    )
    updated_bundle: dict = Field(
        description="If link_found is true, returns the FHIR bundle with updated"
        " references to existing Personresource. If link_found is false, "
        "returns the FHIR bundle with a reference to a newly created "
        "Person resource."
    )
    message: Optional[str] = Field(
        description="An optional message in the case that the linkage endpoint did "
        "not run successfully containing a description of the error that happened.",
        default="",
    )


class LinkInput(BaseModel):
    """
    Schema for requests to the /linking endpoint.
    """

    record: schemas.PIIRecord = Field(description="A PIIRecord to be checked")
    algorithm: Optional[str] = Field(
        description="Optionally, a string that maps to an algorithm label stored in "
        "algorithm table",
        default=None,
    )
    external_person_id: Optional[str] = Field(
        description="The External Identifier, provided by the client,"
        " for a unique patient/person that is linked to patient(s)",
        default=None,
    )


class LinkResponse(BaseModel):
    """
    Schema for requests to the /link endpoint.
    """

    is_match: bool = Field(
        description="A true value indicates that one or more existing records "
        "matched with the provided record, and these results have been linked."
    )
    patient_reference_id: uuid.UUID = Field(
        description="The unique identifier for the patient that has been linked"
    )
    person_reference_id: uuid.UUID = Field(
        description="The identifier for the person that the patient record has " "been linked to.",
    )


class HealthCheckResponse(BaseModel):
    """
    The schema for response from the record linkage health check endpoint.
    """

    status: str = Field(description="Returns status of this service")


@app.get("/")
async def health_check(db_session: orm.Session = Depends(get_session)) -> HealthCheckResponse:
    """
    Check the status of this service and its connection to Master Patient Index(MPI). If
    an HTTP 200 status code is returned along with '{"status": "OK"}' then the record
    linkage service is available and running properly. The mpi_connection_status field
    contains a description of the connection health to the MPI database.
    """
    try:
        db_session.execute(expression.text("SELECT 1")).all()
        return HealthCheckResponse(status="OK")
    except Exception:
        raise HTTPException(status_code=503, detail={"status": "Service Unavailable"})


# Sample requests and responses for docs
# TODO: These assets need to be installed with the python code
sample_link_record_requests = utils.read_json("assets", "sample_link_record_requests.json")
sample_link_record_responses = utils.read_json("assets", "sample_link_record_responses.json")


@app.post("/link-record", status_code=200, responses={200: sample_link_record_responses})
async def link_record(
    request: Request,
    input: Annotated[LinkRecordInput, Body(examples=sample_link_record_requests)],
    response: Response,
    db_session: orm.Session = Depends(get_session),
) -> LinkRecordResponse:
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
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return LinkRecordResponse(
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
        response.status_code = status.HTTP_400_BAD_REQUEST
        return LinkRecordResponse(
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
        return LinkRecordResponse(found_match=found_match, updated_bundle=updated_bundle)

    except ValueError as err:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return LinkRecordResponse(
            found_match=False,
            updated_bundle=input_bundle,
            message=f"Could not connect to database: {err}",
        )


@app.post("/link")
async def link_piirecord(
    request: Request,
    input: Annotated[LinkInput, Body()],
    response: Response,
    db_session: orm.Session = Depends(get_session),
) -> LinkResponse:
    """
    Compare a PII Reocrd with records in the Master Patient Index (MPI) to
    check for matches with existing patient records If matches are found,
    returns the patient and person reference id's
    """
    pii_record = input.record

    external_id = input.external_person_id

    if input.algorithm:
        algorithm = algorithm_service.get_algorithm(db_session, input.algorithm)
    else:
        algorithm = algorithm_service.default_algorithm(db_session)

    if not algorithm:
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        raise HTTPException(status_code=422, detail="Error: Invalid algorithm specified")

    # link the record
    try:
        # Make a copy of record_to_link so we don't modify the original
        record = copy.deepcopy(pii_record)
        (found_match, new_person_id, patient_reference_id) = link.link_record_against_mpi(
            record=record,
            session=db_session,
            algorithm=algorithm,
            external_person_id=external_id,
        )
        return LinkResponse(
            is_match=found_match,
            patient_reference_id=patient_reference_id,
            person_reference_id=new_person_id,
        )

    except ValueError:
        response.status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=400, detail="Error: Bad request")

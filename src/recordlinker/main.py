import copy
from pathlib import Path
from typing import Annotated
from typing import Optional

from fastapi import Body
from fastapi import HTTPException
from fastapi import Response
from fastapi import status
from pydantic import BaseModel
from pydantic import Field

from recordlinker import models
from recordlinker.base_service import BaseService
from recordlinker.config import settings
from recordlinker.linkage.algorithms import DIBBS_BASIC
from recordlinker.linkage.algorithms import DIBBS_ENHANCED
from recordlinker.linkage.link import add_person_resource
from recordlinker.linkage.link import link_record_against_mpi
from recordlinker.linkage.mpi import DIBBsMPIConnectorClient
from recordlinker.linking import mpi_service
from recordlinker.utils import read_json_from_assets
from recordlinker.utils import run_migrations

# Ensure MPI is configured as expected.
run_migrations()
MPI_CLIENT = DIBBsMPIConnectorClient()
# Instantiate FastAPI via DIBBs' BaseService class
app = BaseService(
    service_name="DIBBs Record Linkage Service",
    service_path="/record-linkage",
    description_path=Path(__file__).parent.parent.parent / "README.md",
    include_health_check_endpoint=False,
    # openapi_url="/record-linkage/openapi.json",
).start()

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
        default=None
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


class HealthCheckResponse(BaseModel):
    """
    The schema for response from the record linkage health check endpoint.
    """

    status: str = Field(description="Returns status of this service")

    mpi_connection_status: str = Field(
        description="Returns status of connection to Master Patient Index(MPI)"
    )


@app.get("/")
async def health_check() -> HealthCheckResponse:
    """
    Check the status of this service and its connection to Master Patient Index(MPI). If
    an HTTP 200 status code is returned along with '{"status": "OK"}' then the record
    linkage service is available and running properly. The mpi_connection_status field
    contains a description of the connection health to the MPI database.
    """

    try:
        mpi_client = DIBBsMPIConnectorClient()  # noqa: F841
    except Exception as err:
        # Return a 503 status code with an error message
        msg = {"status": "Service Unavailable", "mpi_connection_status": str(err)}
        raise HTTPException(status_code=503, detail=msg)
    return {"status": "OK", "mpi_connection_status": "OK"}


# Sample requests and responses for docs
sample_link_record_requests = read_json_from_assets("sample_link_record_requests.json")
sample_link_record_responses = read_json_from_assets(
    "sample_link_record_responses.json"
)


@app.post(
    "/link-record", status_code=200, responses={200: sample_link_record_responses}
)
async def link_record(
    input: Annotated[LinkRecordInput, Body(examples=sample_link_record_requests)],
    response: Response,
) -> LinkRecordResponse:
    """
    Compare a FHIR bundle with records in the Master Patient Index (MPI) to
    check for matches with existing patient records If matches are found,
    returns the bundle with updated references to existing patients.
    """

    input = dict(input)
    input_bundle = input.get("bundle", {})
    external_id = input.get("external_person_id", None)

    # Check that DB type is appropriately set up as Postgres so
    # we can fail fast if it's not
    if not settings.db_uri.startswith("postgres"):
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return {
            "found_match": False,
            "updated_bundle": input_bundle,
            "message": f"Unsupported database {settings.db_uri} supplied. "
            + "Make sure your environment variables include an entry "
            + "for `mpi_db_type` and that it is set to 'postgres'.",
        }

    # Determine which algorithm to use; default is DIBBS basic
    algorithm_label = input.get("algorithm")
    session = models.get_session()
    algorithm = mpi_service.get_algorithm_by_label(session, algorithm_label)

    if algorithm is None:
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return {
            "message": "Error: Invalid algorithm specified"
        }
    
    if algorithm.label == "DIBBS_ENHANCED":
        algo_config = DIBBS_ENHANCED   
    else: 
        algo_config = DIBBS_BASIC 

    # Now extract the patient record we want to link
    try:
        record_to_link = [
            entry.get("resource")
            for entry in input_bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType", "") == "Patient"
        ][0]
    except IndexError:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "found_match": False,
            "updated_bundle": input_bundle,
            "message": "Supplied bundle contains no Patient resource to link on.",
        }

    # Now link the record
    try:
        # Make a copy of record_to_link so we don't modify the original
        record = copy.deepcopy(record_to_link)
        (found_match, new_person_id) = link_record_against_mpi(
            record=record,
            algo_config=algo_config,
            external_person_id=external_id,
            mpi_client=MPI_CLIENT,
        )
        updated_bundle = add_person_resource(
            new_person_id, record_to_link.get("id", ""), input_bundle
        )
        return {"found_match": found_match, "updated_bundle": updated_bundle}

    except ValueError as err:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "found_match": False,
            "updated_bundle": input_bundle,
            "message": f"Could not connect to database: {err}",
        }

@app.get("/algorithms")
async def get_algorithms():
    """
    Get a list of all available algorithms from the database
    """
    session = models.get_session()
    algorithmsList = mpi_service.get_all_algorithms(session)

    return {"algorithms": algorithmsList}


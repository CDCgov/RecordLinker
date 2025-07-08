import fastapi
import pydantic
import sqlalchemy
from fastapi import responses
from sqlalchemy import orm

from recordlinker import middleware
from recordlinker._version import __version__
from recordlinker.config import settings
from recordlinker.database import get_session
from recordlinker.routes.algorithm_router import router as algorithm_router
from recordlinker.routes.link_router import router as link_router
from recordlinker.routes.patient_router import router as patient_router
from recordlinker.routes.person_router import router as person_router
from recordlinker.routes.seed_router import router as seed_router
from recordlinker.routes.tuning_router import router as tuning_router


def path(path: str) -> str:
    """
    Add the API root path to the path.
    """
    return f"{settings.api_root_path}{path}"


app = fastapi.FastAPI(
    title="Record Linker",
    version=__version__,
    docs_url=path("/docs"),
    redoc_url=path("/redoc"),
    openapi_url=path("/openapi.json"),
    contact={
        "name": "CDC Public Health Data Infrastructure",
        "url": "https://github.com/CDCgov/RecordLinker",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
    },
    summary="""
        The RecordLinker is a service that links records from two datasets based on a set
        of common attributes. The service is designed to be used in a variety of public
        health contexts, such as linking patient records from different sources or linking
        records from different public health surveillance systems. The service uses a
        probabilistic record linkage algorithm to determine the likelihood that two
        records refer to the same entity. The service is implemented as a RESTful API that
        can be accessed over HTTP. The API provides endpoints for uploading datasets,
        configuring the record linkage process, and retrieving the results of the record
        linkage process.
    """.strip(),
)

app.add_middleware(middleware.CorrelationIdMiddleware)
app.add_middleware(middleware.AccessLogMiddleware)
app.add_exception_handler(Exception, middleware.error_handler)


@app.get("/", include_in_schema=False)
def root():
    """
    Redirect to the OpenAPI documentation.
    """
    return responses.RedirectResponse(url=path("/redoc"))


class HealthCheckResponse(pydantic.BaseModel):
    """
    The schema for the response from the health check endpoint.
    """

    status: str


@app.get(
    path(""),
    name="health-check",
    responses={
        200: {
            "description": "Successful response with status OK",
            "content": {"application/json": {"example": {"status": "OK"}}},
        },
        503: {
            "description": "Service Unavailable",
            "content": {"application/json": {"example": {"detail": "Service Unavailable"}}},
        },
    },
)
async def health_check(
    db_session: orm.Session = fastapi.Depends(get_session),
) -> HealthCheckResponse:
    """
    Check the status of this service and its connection to the database.
    """
    try:
        db_session.execute(sqlalchemy.text("SELECT 1")).all()
        return HealthCheckResponse(status="OK")
    except Exception:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Unavailable",
        )


app.include_router(link_router, prefix=path(""), tags=["link"])
app.include_router(algorithm_router, prefix=path("/algorithm"), tags=["algorithm"])
app.include_router(person_router, prefix=path("/person"), tags=["mpi"])
app.include_router(patient_router, prefix=path("/patient"), tags=["mpi"])
app.include_router(seed_router, prefix=path("/seed"), tags=["mpi"])
if settings.tuning_enabled:
    app.include_router(tuning_router, prefix=path("/tuning"), tags=["tuning"])

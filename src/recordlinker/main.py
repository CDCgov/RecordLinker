import fastapi
import pydantic
import sqlalchemy
from sqlalchemy import orm

from recordlinker import middleware
from recordlinker.database import get_session
from recordlinker.routes.algorithm_router import router as algorithm_router
from recordlinker.routes.link_router import router as link_router

try:
    from recordlinker._version import __version__
except ImportError:
    __version__ = "0.0.0"

app = fastapi.FastAPI(
    title="Record Linker",
    version=__version__,
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


class HealthCheckResponse(pydantic.BaseModel):
    """
    The schema for the response from the health check endpoint.
    """

    status: str


@app.get(
    "/",
    responses={
        200: {
            "description": "Successful response with status OK",
            "content": {"application/json": {"example": {"status": "OK"}}},
        },
        503: {
            "description": "Service Unavailable",
            "content": {"application/json": {"example": {"status": "Service Unavailable"}}},
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
        return {"status": "OK"}
    except Exception:
        msg = {"status": "Service Unavailable"}
        raise fastapi.HttpException(
            status_code=fastapi.status.HTTP_503_SERVICE_UNAVAILABLE, detail=msg
        )


app.include_router(algorithm_router, prefix="/algorithm", tags=["algorithm"])
app.include_router(link_router, prefix="/link", tags=["link"])

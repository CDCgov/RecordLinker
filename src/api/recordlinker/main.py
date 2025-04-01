import os

import fastapi
import pydantic
import sqlalchemy
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import orm
from starlette.responses import FileResponse

from recordlinker import middleware
from recordlinker.config import settings
from recordlinker._version import __version__
from recordlinker.database import get_session
from recordlinker.routes.algorithm_router import router as algorithm_router
from recordlinker.routes.link_router import router as link_router
from recordlinker.routes.patient_router import router as patient_router
from recordlinker.routes.person_router import router as person_router
from recordlinker.routes.seed_router import router as seed_router


async def not_found(request, exc):
    return FileResponse("src/api/recordlinker/wwwroot/404.html")


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
    exception_handlers={
        404: not_found,
    },
)

app.add_middleware(middleware.CorrelationIdMiddleware)
app.add_middleware(middleware.AccessLogMiddleware)
if settings.ui_host:
    # Add CORS for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.ui_host],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# API sub app

subapi = fastapi.FastAPI()

subapi.include_router(link_router, tags=["link"])
subapi.include_router(algorithm_router, prefix="/algorithm", tags=["algorithm"])
subapi.include_router(person_router, prefix="/person", tags=["mpi"])
subapi.include_router(patient_router, prefix="/patient", tags=["mpi"])
subapi.include_router(seed_router, prefix="/seed", tags=["mpi"])


class HealthCheckResponse(pydantic.BaseModel):
    """
    The schema for the response from the health check endpoint.
    """

    status: str


@subapi.get(
    "/",
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


app.mount("/api", subapi)

# SPA
# Bundles integration
app.mount(
    "/_next", StaticFiles(directory="src/api/recordlinker/wwwroot/_next"), name="SpaStaticAssets"
)


# Page routes
@app.get("/wizard")
async def read_page():
    return FileResponse("src/api/recordlinker/wwwroot/wizard.html")


@app.get("/")
async def read_page():
    return FileResponse("src/api/recordlinker/wwwroot/index.html")

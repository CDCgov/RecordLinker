from pathlib import Path

from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import Field
from sqlalchemy import orm
from sqlalchemy.sql import expression

from recordlinker import middleware
from recordlinker.base_service import BaseService
from recordlinker.database import get_session
from recordlinker.routes.algorithm_router import router as algorithm_router
from recordlinker.routes.link_router import router as link_router

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
app.include_router(link_router, prefix="/link", tags=["link"])


# Request and response models


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

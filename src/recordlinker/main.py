from pathlib import Path

import fastapi
import sqlalchemy
from sqlalchemy import orm

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
) -> fastapi.responses.JSONResponse:
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

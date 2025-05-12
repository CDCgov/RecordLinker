"""
recordlinker.routes.health_router
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements health check endpoints for the RecordLinker API.
"""

import fastapi
import pydantic
import sqlalchemy
import sqlalchemy.orm as orm

from recordlinker.database import get_session

router = fastapi.APIRouter()


class HealthCheckResponse(pydantic.BaseModel):
    """
    The schema for the response from the health check endpoint.
    """

    status: str


@router.get(
    "",
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

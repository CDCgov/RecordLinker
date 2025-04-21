"""
recordlinker.routes.demo_router
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the demo router for the RecordLinker API. Exposing
the API endpoints for the demo UI.
"""

import fastapi

from recordlinker import schemas

router = fastapi.APIRouter()


@router.get(
    "/record",
    summary="Get record queue demo data",
    response_model=schemas.DemoData,
)
async def get_demo_data():
    """
    Retrieve static data asset for the record queue page in the demo UI.
    """
    pass  # Replace with actual implementation

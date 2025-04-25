"""
recordlinker.routes.demo_router
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the demo router for the RecordLinker API. Exposing
the API endpoints for the demo UI.
"""

import typing

import fastapi

from recordlinker import schemas
from recordlinker.utils import path as utils

router = fastapi.APIRouter()

# Load static data for the Match Queue page in the demo UI
data = utils.read_json("assets/demo_data.json")["demo_data"]


def filter_and_sort(
    data: typing.Dict,
    status: typing.Optional[schemas.demo.LinkedStatus] = None,
) -> typing.List[schemas.demo.MatchReviewRecord]:
    """
    Filter data by linked status and sort by received_on date.
    """
    status_filters = {
        schemas.demo.LinkedStatus.linked: lambda d: d["linked"] is True,
        schemas.demo.LinkedStatus.unlinked: lambda d: d["linked"] is False,
        schemas.demo.LinkedStatus.evaluated: lambda d: d["linked"] is not None,
        schemas.demo.LinkedStatus.pending: lambda d: d["linked"] is None,
    }

    filtered = [d for d in data if status_filters[status](d)] if status else data
    sorted_data = sorted(
        filtered,
        key=lambda x: x["incoming_record"]["received_on"],
    )
    return [schemas.demo.MatchReviewRecord(**item) for item in sorted_data]


@router.get(
    "/record",
    summary="Get demo records for match queue",
)
def get_demo_data(
    status: typing.Optional[schemas.demo.LinkedStatus] = None,
) -> typing.List[schemas.demo.MatchReviewRecord]:
    """
    Retrieve static data asset for the Match Queue page in the demo UI.
    """
    filtered_sorted = filter_and_sort(data, status)

    return filtered_sorted


@router.get(
    "/record/{patient_reference_id}",
    summary="Get demo records for match review",
)
def get_match_review_records(
    patient_reference_id: int,
) -> schemas.demo.MatchReviewRecord:
    """
    Retrieve static data asset for the Match Review page in the demo UI by pateint_reference_id.
    """

    match_review_record = next(
        (d for d in data if d["incoming_record"]["patient_id"] == patient_reference_id), None
    )
    if match_review_record is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)
    return match_review_record

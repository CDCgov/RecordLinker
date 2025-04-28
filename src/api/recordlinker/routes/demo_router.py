"""
recordlinker.routes.demo_router
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the demo router for the RecordLinker API. Exposing
the API endpoints for the demo UI.
"""

import typing

import fastapi

from recordlinker import schemas
from recordlinker import session_store
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


@router.post(
    "/record/{patient_reference_id}/link",
    summary="Link demo records for match review",
)
def link_match(
    patient_reference_id: int,
    response: fastapi.Response,
) -> schemas.demo.MatchReviewRecord:
    """
    Link demo records for match review.
    """

    match_review_record = next(
        (d for d in data if d["incoming_record"]["patient_id"] == patient_reference_id), None
    )
    if match_review_record is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)

    # Update the linked status
    match_review_record["linked"] = True
    # Update the incoming record with the person_id from the potential match
    match_review_record["incoming_record"]["person_id"] = match_review_record["potential_match"][0][
        "person_id"
    ]

    # Save session (modifies the real response)
    session_store.save_session(
        response,
        key=f"linked_status_{patient_reference_id}",
        data=match_review_record,
    )
    return match_review_record


@router.post(
    "/record/{patient_reference_id}/unlink",
    summary="Unlink demo records for match review",
)
def unlink_match(
    patient_reference_id: int,
    response: fastapi.Response,
) -> schemas.demo.MatchReviewRecord:
    """
    Unlink demo records for match review.
    """

    match_review_record = next(
        (d for d in data if d["incoming_record"]["patient_id"] == patient_reference_id), None
    )
    if match_review_record is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)

    # Update the linked status
    match_review_record["linked"] = False
    # TODO: Remove potential match from the match_review_record since they were deemed not a match

    # Save session
    session_store.save_session(
        response,
        key=f"linked_status_{patient_reference_id}",
        data=match_review_record,
    )
    return match_review_record


@router.get(
    "/record/{patient_reference_id}/linked_status",
    summary="Check linked status from session",
)
def get_linked_status(
    patient_reference_id: int,
    request: fastapi.Request,
) -> schemas.demo.MatchReviewRecord:
    """
    Get linked status from session.
    """
    session_data = session_store.load_session(
        request,
        key=f"linked_status_{patient_reference_id}",
    )
    if session_data is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND, detail="No session data found."
        )

    return session_data

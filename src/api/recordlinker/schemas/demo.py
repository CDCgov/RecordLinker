"""
recordlinker.schemas.demo
~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the schema definitions for the demo API endpoints.

"""

import datetime
import enum
import typing

import pydantic

from recordlinker import schemas


class DataStream(pydantic.BaseModel):
    system: str = pydantic.Field(description="The originating system of the data stream.")
    type: str = pydantic.Field(description="The type of the data stream.")


class MatchQueueRecord(pydantic.BaseModel):
    """
    Schema for a demo record on the Record Queue page.
    """

    id: int = pydantic.Field(
        description="The unique identifier for the record.",
    )
    first_name: str = pydantic.Field(
        description="The first name of the person.",
    )
    last_name: str = pydantic.Field(
        description="The last name of the person.",
    )
    birth_date: datetime.date = pydantic.Field(
        validation_alias=pydantic.AliasChoices("birth_date", "birthdate", "birthDate")
    )
    received_on: datetime.datetime = pydantic.Field(
        description="The date and time when the record was received.",
    )
    data_stream: DataStream = pydantic.Field(
        description="The data stream associated with the record.",
    )
    link_score: typing.Annotated[float, pydantic.Field(ge=0, le=1)] = pydantic.Field(
        description="The confidence score between 0 and 1 for the linkage."
    )
    linked: bool | None = pydantic.Field(
        description="Whether the record has been linked to another entity."
    )


class LinkedStatus(enum.Enum):
    """
    Enum for the status of a record in the demo API that is used to filter records on
    the Record Queue page.
    """

    linked = "linked"
    unlinked = "unlinked"
    evaluated = "evaluated"
    pending = "pending"


class MatchReviewRecordData(pydantic.BaseModel):
    """
    Schema for the data associated with a match review record.
    """

    person_id: int | None = pydantic.Field(
        description="The unique identifier for the person associated with the record.",
        default=None,
    )
    patient_id: int = pydantic.Field(
        "The unique identifier for the patient associated with the record."
    )
    first_name: str = pydantic.Field(
        description="The first name of the patient.",
    )
    last_name: str = pydantic.Field(
        description="The last name of the patient.",
    )
    mrn: str = pydantic.Field(
        description="The social security number of the patient.",
    )
    birth_date: typing.Optional[datetime.date] = pydantic.Field(
        default=None, validation_alias=pydantic.AliasChoices("birth_date", "birthdate", "birthDate")
    )
    address: schemas.pii.Address = pydantic.Field(
        description="The address of the patient.",
    )


class MatchReviewRecord(MatchQueueRecord):
    """
    Schema for a demo record on the Match Review page.
    """

    incoming_data: MatchReviewRecordData = pydantic.Field(
        description="The incoming patient data that is being reviewed."
    )
    potential_match: MatchReviewRecordData = pydantic.Field(
        description="The potential match details for the record."
    )

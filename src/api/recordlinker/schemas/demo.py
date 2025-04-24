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


class LinkedStatus(enum.Enum):
    """
    Enum for the status of a record in the demo API that is used to filter records on
    the Record Queue page.
    """

    linked = "linked"
    unlinked = "unlinked"
    evaluated = "evaluated"
    pending = "pending"


class DataStream(pydantic.BaseModel):
    system: str = pydantic.Field(description="The originating system of the data stream.")
    type: str = pydantic.Field(description="The type of the data stream.")


class Patient(pydantic.BaseModel):
    """
    Base schema for a patient record.
    """

    patient_id: int = pydantic.Field(
        description="The unique identifier for the patient associated with the record."
    )
    first_name: typing.Optional[str] = pydantic.Field(
        description="The first name of the patient.",
    )
    last_name: typing.Optional[str] = pydantic.Field(
        description="The last name of the patient.",
    )
    mrn: typing.Optional[str] = pydantic.Field(
        description="The medical record number of the patient.",
    )
    birth_date: typing.Optional[datetime.date] = pydantic.Field(
        default=None, validation_alias=pydantic.AliasChoices("birth_date", "birthdate", "birthDate")
    )
    address: typing.Optional[schemas.pii.Address] = pydantic.Field(
        description="The address of the patient.",
    )
    received_on: typing.Optional[datetime.datetime] = pydantic.Field(
        description="The date and time when the record was received.", default=None
    )
    data_stream: typing.Optional[DataStream] = pydantic.Field(
        description="The data stream associated with the record.", default=None
    )


class IncomingRecord(Patient):
    """
    Schema for the incoming data associated with a match review record.
    """

    person_id: int | None = pydantic.Field(
        description="The unique identifier for the person associated with the record.",
        default=None,
    )


class PotentialMatch(pydantic.BaseModel):
    """
    Schema for a potential match record.
    """

    person_id: int = pydantic.Field(
        description="The unique identifier for the person associated with the record.",
    )
    link_score: typing.Annotated[float, pydantic.Field(ge=0, le=1)] = pydantic.Field(
        description="The confidence score between 0 and 1 for the linkage."
    )
    patients: typing.List[Patient] = pydantic.Field(
        description="The list of potential match patient records.",
    )


class MatchReviewRecord(pydantic.BaseModel):
    """
    Schema for a demo record on the Match Review page.
    """

    linked: bool | None = pydantic.Field(
        description="Whether the record has been linked to another entity."
    )
    incoming_record: IncomingRecord = pydantic.Field(
        description="The incoming patient data that is being reviewed."
    )
    potential_match: typing.Optional[typing.List[PotentialMatch]] = pydantic.Field(
        description="The potential match details for the record.",
        default=None,
    )

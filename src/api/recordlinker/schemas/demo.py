"""
recordlinker.schemas.demo
~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the schema definitions for the demo API endpoints.

"""

import datetime
import typing

import pydantic


class DataStream(pydantic.BaseModel):
    system: str = pydantic.Field(description="The originating system of the data stream.")
    type: str = pydantic.Field(description="The type of the data stream.")


class Record(pydantic.BaseModel):
    """
    Schema for a demo record.
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
    linked: bool = pydantic.Field(
        default=None, description="Whether the record has been linked to another entity."
    )

"""
recordlinker.schemas.link
~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the schema definitions for the link API endpoints.
"""

import typing
import uuid

import pydantic

from recordlinker.schemas.pii import PIIRecord


class LinkInput(pydantic.BaseModel):
    """
    Schema for requests to the link endpoint
    """

    record: PIIRecord = pydantic.Field(description="A PIIRecord to be checked")
    algorithm: typing.Optional[str] = pydantic.Field(
        description="Optionally, a string that maps to an algorithm label stored in "
        "algorithm table",
        default=None,
    )
    external_person_id: typing.Optional[str] = pydantic.Field(
        description="The External Identifier, provided by the client,"
        " for a unique patient/person that is linked to patient(s)",
        default=None,
    )


class LinkResponse(pydantic.BaseModel):
    """
    Schema for responses from the link endpoint.
    """

    is_match: bool = pydantic.Field(
        description="A true value indicates that one or more existing records "
        "matched with the provided record, and these results have been linked."
    )
    patient_reference_id: uuid.UUID = pydantic.Field(
        description="The unique identifier for the patient that has been linked"
    )
    person_reference_id: uuid.UUID = pydantic.Field(
        description="The identifier for the person that the patient record has " "been linked to.",
    )


class LinkFhirInput(pydantic.BaseModel):
    """
    Schema for requests to the link FHIR endpoint.
    """

    bundle: dict = pydantic.Field(
        description="A FHIR bundle containing a patient resource to be checked "
        "for links to existing patient records"
    )
    algorithm: typing.Optional[str] = pydantic.Field(
        description="Optionally, a string that maps to an algorithm label stored in "
        "algorithm table",
        default=None,
    )
    external_person_id: typing.Optional[str] = pydantic.Field(
        description="The External Identifier, provided by the client,"
        " for a unique patient/person that is linked to patient(s)",
        default=None,
    )


class LinkFhirResponse(pydantic.BaseModel):
    """
    The schema for responses from the link FHIR endpoint.
    """

    found_match: bool = pydantic.Field(
        description="A true value indicates that one or more existing records "
        "matched with the provided record, and these results have been linked."
    )
    updated_bundle: dict = pydantic.Field(
        description="If link_found is true, returns the FHIR bundle with updated"
        " references to existing Personresource. If link_found is false, "
        "returns the FHIR bundle with a reference to a newly created "
        "Person resource."
    )
    message: typing.Optional[str] = pydantic.Field(
        description="An optional message in the case that the linkage endpoint did "
        "not run successfully containing a description of the error that happened.",
        default="",
    )

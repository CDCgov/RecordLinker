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


class LinkResult(pydantic.BaseModel):
    """
    TODO
    """

    person_reference_id: uuid.UUID = pydantic.Field(
        description="The identifier for a person that the patient may be linked to."
    )

    belongingness_ratio: float = pydantic.Field(
        description="The percentage of patient records matched in this person cluster."
    )


    @pydantic.model_validator(mode="before")
    @classmethod
    def extract_person_reference_id(cls, data: typing.Any) -> typing.Any:
        """
        Extract the person_reference_id from the person_reference_id field.
        """
        person = data.pop("person", None)
        if person:
            data["person_reference_id"] = person.reference_id
        return data


class LinkResponse(pydantic.BaseModel):
    """
    Schema for responses from the link endpoint.
    """

    
    patient_reference_id: uuid.UUID = pydantic.Field(
        description="The unique identifier for the patient that has been linked."
    )
    person_reference_id: uuid.UUID | None = pydantic.Field(
        description="The identifier for the person that the patient record has been linked to.",
    )
    results: list[LinkResult] = pydantic.Field(
        description="A list of (possibly) matched Persons. If prediction='match', either the single"
                    "(include_multiple_matches=False) or multiple (include_multiple_matches=True) "
                    "Persons with which the Patient record matches. If prediction='possible_match',"
                    "all Persons with which the Patient record possibly matches."
    )

    @pydantic.computed_field
    @property
    def prediction(self) -> typing.Literal["match", "possible_match", "no_match"]:
        """
        Record Linkage algorithm prediction.
        """
        print(f"self.results: {self.results}")
        if self.person_reference_id and self.results:
            return "match"
        elif not self.results:
            return "no_match"
        else:
            return "possible_match"


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


class LinkFhirResponse(LinkResponse):
    """
    The schema for responses from the link FHIR endpoint.
    """

    updated_bundle: dict | None = pydantic.Field(
        description="If 'prediction' is 'match', returns the FHIR bundle with updated"
        " references to existing Person resource. If 'prediction' is 'no_match', "
        "returns the FHIR bundle with a reference to a newly created "
        "Person resource. If 'prediction' is 'possible_match', returns None."
    )

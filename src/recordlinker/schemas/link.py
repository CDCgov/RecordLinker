"""
recordlinker.schemas.link
~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the schema definitions for the link API endpoints.
"""

import typing
import uuid

import pydantic

from recordlinker.schemas.pii import PIIRecord

Prediction = typing.Literal["certain", "possible", "certainly-not"]


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
    Schema for linkage results to a person cluster.
    """

    person_reference_id: uuid.UUID = pydantic.Field(
        description="The identifier for a person that the patient may be linked to."
    )
    accumulated_points: float = pydantic.Field(
        description="The median number of log-odds points accumulated by the blocked patients "
        "belonging to this Person Cluster when compared to an incoming record."
    )
    rms: typing.Annotated[float, pydantic.Field(ge=0, le=1)] = pydantic.Field(
        description="The Relative Match Strength (normalized between 0 and 1) of this "
        "Person Cluster to an in coming record."
    )
    mmt: typing.Annotated[float, pydantic.Field(ge=0, le=1)] = pydantic.Field(
        description="The Minimum Match Threshold (normalized between 0 and 1) used in "
        "the linkage pass whose score this Result captures."
    )
    cmt: typing.Annotated[float, pydantic.Field(ge=0, le=1)] = pydantic.Field(
        description="The Certain Match Threshold (normalized between 0 and 1) used "
        "in the linkage pass whose score this Result captures."
    )
    grade: str = pydantic.Field(
        description="The FHIR-corresponding Match-Grade assigned to the pass-specific "
        "score measured by this Result."
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


class MatchResponse(pydantic.BaseModel):
    """
    Schema for responses from the match endpoint.
    """

    prediction: Prediction
    person_reference_id: uuid.UUID | None = pydantic.Field(
        description="The identifier for the person that the patient record has been matched to."
        ' If prediction="possible_match", this value will be null.'
    )
    results: list[LinkResult] = pydantic.Field(
        description="A list of (possibly) matched Persons. If prediction='match', either the single"
        "(include_multiple_matches=False) or multiple (include_multiple_matches=True) "
        "Persons with which the Patient record matches. If prediction='possible_match',"
        "all Persons with which the Patient record possibly matches."
    )


class LinkResponse(MatchResponse):
    """
    Schema for responses from the link endpoint.
    """

    patient_reference_id: uuid.UUID = pydantic.Field(
        description="The unique identifier for the patient that has been linked."
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


class MatchFhirResponse(MatchResponse):
    """
    The schema for responses from the match FHIR endpoint.
    """

    updated_bundle: dict | None = pydantic.Field(
        description="If 'prediction' is 'match', returns the FHIR bundle with updated"
        " references to existing Person resource. If 'prediction' is 'no_match' or"
        " 'possible_match', returns null."
    )


class LinkFhirResponse(LinkResponse):
    """
    The schema for responses from the link FHIR endpoint.
    """

    updated_bundle: dict | None = pydantic.Field(
        description="If 'prediction' is 'match', returns the FHIR bundle with updated"
        " references to existing Person resource. If 'prediction' is 'no_match', "
        "returns the FHIR bundle with a reference to a newly created "
        "Person resource. If 'prediction' is 'possible_match', returns null."
    )

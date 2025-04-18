"""
recordlinker.schemas.algorithm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the schema definitions for the algorithm records.
These are used for parsing and validating algorithm configurations.
"""

import typing

import pydantic
from typing_extensions import Annotated

from recordlinker.linking import matchers
from recordlinker.models.mpi import BlockingKey
from recordlinker.schemas.pii import Feature


class Evaluator(pydantic.BaseModel):
    """
    The schema for an evaluator record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True, use_enum_values=True)

    feature: str = pydantic.Field(json_schema_extra={"enum": Feature.all_options()})
    func: matchers.FeatureFunc

    @pydantic.field_validator("feature", mode="before")
    def validate_feature(cls, value):
        """
        Validate the feature is a valid PII feature.
        """
        try:
            Feature.parse(value)
        except ValueError as e:
            raise ValueError(f"Invalid feature: '{value}'. {e}")
        return value


class AlgorithmPass(pydantic.BaseModel):
    """
    The schema for an algorithm pass record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True, use_enum_values=True)

    label: typing.Optional[str] = pydantic.Field(
        None, pattern=r"^[A-Za-z0-9]+(?:[_-][A-Za-z0-9]+)*$", max_length=255
    )
    description: typing.Optional[str] = None
    blocking_keys: list[BlockingKey] = pydantic.Field(
        ...,
        json_schema_extra={
            "enum": [{"value": k.value, "description": k.description} for k in BlockingKey],
        },
    )
    evaluators: list[Evaluator]
    possible_match_window: tuple[
        Annotated[float, pydantic.Field(ge=0, le=1)], Annotated[float, pydantic.Field(ge=0, le=1)]
    ]
    kwargs: dict[str, typing.Any] = {}

    @pydantic.field_validator("possible_match_window", mode="before")
    def validate_possible_match_window(cls, value):
        """
        Validate the Possible Match Window.
        """
        minimum_match_threshold, certain_match_threshold = value
        if minimum_match_threshold > certain_match_threshold:
            raise ValueError(f"Invalid range. Lower bound must be less than upper bound: {value}")
        return (minimum_match_threshold, certain_match_threshold)
    
    @pydantic.model_validator(mode="after")
    def default_label(self) -> "AlgorithmPass":
        """
        Create a default label for the algorithm based on the keys used in the evaluation step.
        """
        if not self.label:
            blocks = ["BLOCK"] + [str(b).lower() for b in self.blocking_keys]
            matches = ["MATCH"] + [str(e.feature).lower() for e in self.evaluators]
            self.label = "_".join(blocks + matches)
        return self

    @pydantic.field_validator("kwargs", mode="before")
    def validate_kwargs(cls, value):
        """
        Validate the kwargs keys are valid.
        """
        # TODO: possibly a better way to validate is to take two PIIRecords
        # and compare them using the AlgorithmPass.  If it doesn't raise an
        # exception, then the kwargs are valid.
        if value:
            allowed = {k.value for k in matchers.AvailableKwarg}
            # Validate each key in kwargs
            for key, val in value.items():
                if key not in allowed:
                    raise ValueError(f"Invalid kwargs key: '{key}'. Allowed keys are: {allowed}")
        return value


class SkipValue(pydantic.BaseModel):
    feature: str = pydantic.Field(json_schema_extra={"enum": Feature.all_options() + ["*"]})
    values: list[str] = pydantic.Field(min_length=1)

    @pydantic.field_validator("feature", mode="before")
    def validate_feature(cls, value):
        """
        Validate the feature is a valid PII feature.
        """
        if value == "*":
            return value
        try:
            Feature.parse(value)
        except ValueError as e:
            raise ValueError(f"Invalid feature: '{value}'. {e}")
        return value


class Algorithm(pydantic.BaseModel):
    """
    The schema for an algorithm record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True, use_enum_values=True)

    label: str = pydantic.Field(pattern=r"^[A-Za-z0-9]+(?:[_-][A-Za-z0-9]+)*$", max_length=255)
    description: typing.Optional[str] = None
    is_default: bool = False
    include_multiple_matches: bool = True
    passes: typing.Sequence[AlgorithmPass]
    max_missing_allowed_proportion: float = pydantic.Field(ge=0.0, le=1.0)
    missing_field_points_proportion: float = pydantic.Field(ge=0.0, le=1.0)
    skip_values: typing.Sequence[SkipValue] = []


    @pydantic.model_validator(mode="after")
    def validate_passes(self) -> "Algorithm":
        """
        Validate that each pass has a unique label.
        """
        labels = {p.label for p in self.passes}
        if len(labels) != len(self.passes):
            raise ValueError("Each pass must have a unique label.")
        return self


class AlgorithmSummary(Algorithm):
    """
    The schema for a summary of an algorithm record.
    """

    passes: typing.Sequence[AlgorithmPass] = pydantic.Field(exclude=True)

    # mypy doesn't support decorators on properties; https://github.com/python/mypy/issues/1362
    @pydantic.computed_field  # type: ignore[misc]
    @property
    def pass_count(self) -> int:
        """
        Get the number of passes in the algorithm.
        """
        return len(self.passes)

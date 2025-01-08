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

    blocking_keys: list[BlockingKey]
    evaluators: list[Evaluator]
    rule: matchers.RuleFunc
    kwargs: dict[str, typing.Any] = {}

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


class Algorithm(pydantic.BaseModel):
    """
    The schema for an algorithm record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True, use_enum_values=True)

    label: str = pydantic.Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: typing.Optional[str] = None
    is_default: bool = False
    include_multiple_matches: bool = True
    belongingness_ratio: tuple[
        Annotated[float, pydantic.Field(ge=0, le=1)], Annotated[float, pydantic.Field(ge=0, le=1)]
    ]
    passes: typing.Sequence[AlgorithmPass]

    @pydantic.field_validator("belongingness_ratio", mode="before")
    def validate_belongingness_ratio(cls, value):
        """
        Validate the Belongingness Ratio Threshold Range.
        """
        lower_bound, upper_bound = value
        if lower_bound > upper_bound:
            raise ValueError(f"Invalid range. Lower bound must be less than upper bound: {value}")
        return (lower_bound, upper_bound)


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

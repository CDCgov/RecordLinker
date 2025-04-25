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

    model_config = pydantic.ConfigDict(from_attributes=True)

    feature: Feature = pydantic.Field(json_schema_extra={"enum": Feature.all_options()})
    func: matchers.FeatureFunc

    @pydantic.field_validator("feature", mode="before")
    def validate_feature(cls, value: str) -> Feature:
        """
        Validate the feature is a valid PII feature.
        """
        try:
            return Feature.parse(value)
        except ValueError as e:
            raise ValueError(f"Invalid feature: '{value}'. {e}")

    @pydantic.field_serializer("func")
    def serialize_func(self, value: matchers.FeatureFunc) -> str:
        """
        Serialize the func to a string.
        """
        return str(value)


class LogOdd(pydantic.BaseModel):
    """
    The schema for an LogOdd record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    feature: Feature = pydantic.Field(json_schema_extra={"enum": Feature.all_options()})
    value: Annotated[float, pydantic.Field(ge=0)]

    @pydantic.field_validator("feature", mode="before")
    def validate_feature(cls, value):
        """
        Validate the feature is a valid PII feature.
        """
        try:
            return Feature.parse(value)
        except ValueError as e:
            raise ValueError(f"Invalid feature: '{value}'. {e}")


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


class AlgorithmContext(pydantic.BaseModel):
    """
    The schema for an algorithm context record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    include_multiple_matches: bool = True
    log_odds: typing.Sequence[LogOdd] = []
    skip_values: typing.Sequence[SkipValue] = []

    @pydantic.model_validator(mode="after")
    def init_log_odds_helpers(self) -> typing.Self:
        """
        Initialize cache helpers for returning log odds values.
        """
        self._log_odds_cache: dict[str, float | None] = {}
        self._log_odds_mapping: dict[str, float] = {str(o.feature): o.value for o in self.log_odds}
        return self

    def get_log_odds(self, value: Feature | BlockingKey) -> float | None:
        """
        Get the log odds for a specific Feature or BlockingKey.
        """
        key = str(value)
        result: float | None = None

        result = self._log_odds_cache.get(key, None)
        if result:
            return result

        vals = value.values_to_match() if isinstance(value, Feature) else [str(value)]
        for val in vals:
            result = self._log_odds_mapping.get(val, None)
            if result:
                break

        self._log_odds_cache[key] = result
        return result


class AlgorithmPass(pydantic.BaseModel):
    """
    The schema for an algorithm pass record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

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

    @pydantic.field_serializer("blocking_keys")
    def serialize_blocking_keys(self, keys: list[BlockingKey]) -> list[str]:
        """
        Serialize the blocking keys to a list of strings.
        """
        return [str(k) for k in keys]


class Algorithm(pydantic.BaseModel):
    """
    The schema for an algorithm record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True, use_enum_values=True)

    label: str = pydantic.Field(pattern=r"^[A-Za-z0-9]+(?:[_-][A-Za-z0-9]+)*$", max_length=255)
    description: typing.Optional[str] = None
    is_default: bool = False
    algorithm_context: AlgorithmContext = AlgorithmContext()
    passes: typing.Sequence[AlgorithmPass]
    max_missing_allowed_proportion: float = pydantic.Field(ge=0.0, le=1.0)
    missing_field_points_proportion: float = pydantic.Field(ge=0.0, le=1.0)

    @pydantic.model_validator(mode="after")
    def validate_passes(self) -> typing.Self:
        """
        Validate that each pass has a unique label.
        """
        labels = {p.label for p in self.passes}
        if len(labels) != len(self.passes):
            raise ValueError("Each pass must have a unique label.")
        return self

    @pydantic.model_validator(mode="after")
    def validate_log_odds_defined(self) -> typing.Self:
        """
        Check that log odds values are defined for all blocking keys and evaluators.
        """
        for pass_ in self.passes:
            for blocking_key in pass_.blocking_keys:
                if not self.algorithm_context.get_log_odds(blocking_key):
                    raise ValueError("Log odds must be defined for all blocking keys.")
            for evaluator in pass_.evaluators:
                if not self.algorithm_context.get_log_odds(evaluator.feature):
                    raise ValueError("Log odds must be defined for all evaluators.")
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

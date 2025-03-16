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
from recordlinker.models.mpi import Patient
from recordlinker.schemas.pii import Feature
from recordlinker.schemas.pii import PIIRecord


class Defaults(pydantic.BaseModel):
    """
    Advanced values with good defaults. Please override with caution.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    fuzzy_match_threshold: Annotated[float, pydantic.Field(ge=0, le=1)] = 0.9
    fuzzy_match_measure: matchers.SIMILARITY_MEASURES = "JaroWinkler"


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


class EvaluationContext(pydantic.BaseModel):
    """
    The schema for an evaluation context record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    include_multiple_matches: bool = pydantic.Field(
        default=True,
        description="Whether to include multiple results if more than one cluster is identified above the upper threshold.",
    )
    belongingness_ratio: tuple[
        Annotated[float, pydantic.Field(ge=0, le=1)], Annotated[float, pydantic.Field(ge=0, le=1)]
    ] = pydantic.Field(
        default=(1.0, 1.0),
        description="The lower and upper bounds of belongingness in which a results is considered a possible or certain match.",
    )
    log_odds: list[LogOdd] = []
    defaults: Defaults = Defaults()

    @pydantic.field_validator("belongingness_ratio", mode="before")
    def validate_belongingness_ratio(cls, value):
        """
        Validate the Belongingness Ratio Threshold Range.
        """
        lower_bound, upper_bound = value
        if lower_bound > upper_bound:
            raise ValueError(f"Invalid range. Lower bound must be less than upper bound: {value}")
        return (lower_bound, upper_bound)

    @pydantic.field_serializer("belongingness_ratio")
    def serialize_belongingness_ratio(self, value: tuple[float, float]) -> list[float]:
        """
        Serialize the belongingness ratio to a list of floats.
        """
        return list(value)

    @property
    def belongingness_ratio_lower_bound(self) -> float:
        """
        The lower bound of the belongingness ratio threshold range.
        """
        return self.belongingness_ratio[0]

    @property
    def belongingness_ratio_upper_bound(self) -> float:
        """
        The upper bound of the belongingness ratio threshold range.
        """
        return self.belongingness_ratio[1]

    def get_log_odds(self, feature: Feature) -> float | None:
        """
        Get the log odds for a specific feature.
        """
        mapping: dict[str, float] = {str(o.feature): o.value for o in self.log_odds}
        for val in feature.values_to_match():
            if val in mapping:
                return mapping[val]
        return None


class Evaluator(pydantic.BaseModel):
    """
    The schema for an evaluator record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    feature: Feature = pydantic.Field(json_schema_extra={"enum": Feature.all_options()})
    func: matchers.FeatureFunc
    fuzzy_match_threshold: Annotated[float, pydantic.Field(ge=0, le=1)] | None = pydantic.Field(
        default=None,
        description="[Optional] Set to override the default fuzzy match threshold for this evaluator.",
    )
    fuzzy_match_measure: matchers.SIMILARITY_MEASURES | None = pydantic.Field(
        default=None,
        description="[Optional] Set to override the default fuzzy match measure for this evaluator.",
    )

    @pydantic.field_validator("feature", mode="before")
    def validate_feature(cls, value):
        """
        Validate the feature is a valid PII feature.
        """
        try:
            return Feature.parse(value)
        except ValueError as e:
            raise ValueError(f"Invalid feature: '{value}'. {e}")

    # TODO: move to link.py????
    def invoke(self, record: PIIRecord, patient: Patient, context: EvaluationContext) -> float:
        ""
        func: typing.Callable = self.func.callable()
        kwargs = {
            "fuzzy_match_threshold": self.fuzzy_match_threshold
            or context.defaults.fuzzy_match_threshold,
            "fuzzy_match_measure": self.fuzzy_match_measure or context.defaults.fuzzy_match_measure,
        }
        log_odds = context.get_log_odds(self.feature)
        return func(record, patient, self.feature, log_odds, **kwargs)

    @pydantic.field_serializer("func")
    def serialize_func(self, value: matchers.FeatureFunc) -> str:
        """
        Serialize the func to a string.
        """
        return str(value)


class AlgorithmPass(pydantic.BaseModel):
    """
    The schema for an algorithm pass record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    blocking_keys: list[BlockingKey] = pydantic.Field(
        ...,
        json_schema_extra={
            "enum": [{"value": k.value, "description": k.description} for k in BlockingKey],
        },
    )
    evaluators: list[Evaluator]
    true_match_threshold: Annotated[float, pydantic.Field(ge=0)]

    @pydantic.field_validator("blocking_keys", mode="before")
    def validate_blocking_keys(cls, value) -> list[BlockingKey]:
        """
        Validate the blocking keys are valid blocking keys.
        """
        try:
            return [getattr(BlockingKey, k) for k in value]
        except AttributeError as e:
            raise ValueError(f"Invalid blocking key: '{value}'. {e}")

    @pydantic.field_serializer("blocking_keys")
    def serialize_blocking_keys(self, value: list[BlockingKey]) -> list[str]:
        """
        Serialize the blocking keys to a list of strings.
        """
        return [k.value for k in value]


class Algorithm(pydantic.BaseModel):
    """
    The schema for an algorithm record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    label: str = pydantic.Field(
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="A unique string used to identify this algorithm.",
    )
    description: typing.Optional[str] = None
    is_default: bool = pydantic.Field(
        default=False,
        description="Whether this is the default algorithm used for linking. Only one algorithm can be the default.",
    )
    evaluation_context: EvaluationContext = EvaluationContext()
    passes: typing.Sequence[AlgorithmPass]

    @pydantic.model_validator(mode="after")
    def validate_log_odds_defined(self) -> typing.Self:
        """
        Check that log odds values are defined for all blocking keys and evaluators.
        """
        for pass_ in self.passes:
            # NOTE: this is a future use case, as we may want to use log odds in our blocking calls
            for blocking_key in pass_.blocking_keys:
                if not self.evaluation_context.get_log_odds(Feature.parse(str(blocking_key))):
                    raise ValueError("Log odds must be defined for all blocking keys.")
            for evaluator in pass_.evaluators:
                if not self.evaluation_context.get_log_odds(evaluator.feature):
                    raise ValueError("Log odds must be defined for all evaluators.")
        return self

    @pydantic.model_validator(mode="after")
    def validate_true_match_threshold(self) -> typing.Self:
        """
        Validate the true match threshold is less than the max evaluator score.
        """
        for pass_ in self.passes:
            max_score = 0.0
            for evaluator in pass_.evaluators:
                max_score += self.evaluation_context.get_log_odds(evaluator.feature) or 0.0
            if pass_.true_match_threshold > max_score:
                raise ValueError(
                    "True match threshold must be less than or equal to the max evaluator score."
                )
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

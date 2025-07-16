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
    fuzzy_match_threshold: Annotated[float, pydantic.Field(ge=0, le=1)] | None = pydantic.Field(
        default=None,
        description="[Optional] Set to override the default fuzzy match threshold for this evaluator.",
    )
    fuzzy_match_measure: matchers.SIMILARITY_MEASURES | None = pydantic.Field(
        default=None,
        description="[Optional] Set to override the default fuzzy match measure for this evaluator.",
    )

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
    value: Annotated[float, pydantic.Field(ge=0)] = pydantic.Field(
        description=(
            "A weight to capture the information value of this field in a healthcare "
            "record for the purpose of patient matching. These values are in reference "
            "to one another, and should be produced by a domain expert who is familiar "
            "with running a log odds training procedure on an existing data set."
        )
    )

    @pydantic.field_validator("feature", mode="before")
    def validate_feature(cls, value):
        """
        Validate the feature is a valid PII feature.
        """
        try:
            return Feature.parse(str(value))
        except ValueError as e:
            raise ValueError(f"Invalid feature: '{value}'. {e}")


class SkipValue(pydantic.BaseModel):
    feature: str = pydantic.Field(json_schema_extra={"enum": Feature.all_options() + ["*"]})
    values: list[str] = pydantic.Field(
        min_length=1,
        description=(
            "A list of values that denote possible field entries that the algorithm should "
            "regard as 'meaningless' and ignore during blocking and evaluation."
        ),
        examples=["John Doe", "unknown", "anonymous"],
    )
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


class AlgorithmAdvanced(pydantic.BaseModel):
    """
    The schema for an advanced algorithm settings.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    fuzzy_match_threshold: Annotated[float, pydantic.Field(ge=0, le=1)] = pydantic.Field(
        default=0.9,
        description=(
            "When using fuzzy matching, the minimum similarity two records must have on a "
            "given field, for that field to contribute to a match. If the similarity meets "
            "or exceeds this threshold, the field contributes its log-odds points towards a "
            "potential match's score. If the similarity is below this threshold, it is set "
            "to zero to avoid the buildup of small errors from weak similarities."
        ),
    )
    fuzzy_match_measure: matchers.SIMILARITY_MEASURES = pydantic.Field(
        default="JaroWinkler",
        description=(
            "The type of fuzzy comparison used when judging how similar a field is across "
            "two patient records."
        ),
    )
    max_missing_allowed_proportion: Annotated[float, pydantic.Field(ge=0.0, le=1.0)] = pydantic.Field(
        default=0.5,
        description=(
            "The proportion of log-odds points that can be missing from a record’s fields "
            "before that record stops being eligible as a potential match. When too many "
            "fields are missing from a record, making match decisions for that record "
            "becomes impossible. This parameter controls the extent to which information "
            "can be absent before some processing is automatically skipped."
        )
    )
    missing_field_points_proportion: Annotated[float, pydantic.Field(ge=0.0, le=1.0)] = pydantic.Field(
        default=0.5,
        description=(
            "The proportion of a field's log-odds points earned when making a comparison "
            "in which at least one record is missing information. This parameter only "
            "applies when a record is missing some field information but does not have more "
            "missingness than permitted by max_missing_allowed_proportion."
        )
    )

class AlgorithmContext(pydantic.BaseModel):
    """
    The schema for an algorithm context record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    include_multiple_matches: bool = pydantic.Field(
        default=True,
        description=(
            "A boolean flag indicating whether the algorithm should return only the "
            "highest scoring match to the caller, or whether it should return all "
            "match candidates who scored an equivalently high grade with the best match."
        )
    )
    log_odds: typing.Sequence[LogOdd] = []
    skip_values: typing.Sequence[SkipValue] = []
    advanced: AlgorithmAdvanced = AlgorithmAdvanced()

    @pydantic.model_validator(mode="after")
    def init_log_odds_helpers(self) -> typing.Self:
        """
        Initialize cache helpers for returning log odds values.
        """
        self._log_odds_mapping: dict[str, float] = {str(o.feature): o.value for o in self.log_odds}
        return self

    def get_log_odds(self, value: Feature | BlockingKey) -> float | None:
        """
        Get the log odds for a specific Feature or BlockingKey.
        """
        result: float | None = None

        vals = value.values_to_match() if isinstance(value, Feature) else [str(value)]
        for val in vals:
            result = self._log_odds_mapping.get(val, None)
            if result:
                break

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
    ] = pydantic.Field(...,
        description=(
            "A range of decimal values consisting of two endpoint thresholds: a Minimum "
            "Match Threshold—representing an RMS value below which a candidate record is "
            "labeled 'certainly-not' a match—and a Certain Match Threshold, an RMS value "
            "above which a candidate record is labeled a 'certain' match."
        )
    )

    def model_post_init(self, __context) -> None:
        """
        Set the default label if one is not provided.
        """
        self.label = self.label or self.default_label

    @property
    def default_label(self) -> str:
        """
        Create a default label for the algorithm based on the keys used in the evaluation step.
        """
        blocks = ["BLOCK"] + [str(b).lower() for b in self.blocking_keys]
        matches = ["MATCH"] + [str(e.feature).lower() for e in self.evaluators]
        return "_".join(blocks + matches)

    @property
    def resolved_label(self) -> str:
        """
        Post initialization a label is always available.
        """
        return self.label # type: ignore[return-value]

    @pydantic.field_validator("possible_match_window", mode="before")
    def validate_possible_match_window(cls, value):
        """
        Validate the Possible Match Window.
        """
        minimum_match_threshold, certain_match_threshold = value
        if minimum_match_threshold > certain_match_threshold:
            raise ValueError(f"Invalid range. Lower bound must be less than upper bound: {value}")
        return (minimum_match_threshold, certain_match_threshold)


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

    algorithm_context: AlgorithmContext = pydantic.Field(exclude=True, default=AlgorithmContext())
    passes: typing.Sequence[AlgorithmPass] = pydantic.Field(exclude=True)

    # mypy doesn't support decorators on properties; https://github.com/python/mypy/issues/1362
    @pydantic.computed_field  # type: ignore[misc]
    @property
    def pass_count(self) -> int:
        """
        Get the number of passes in the algorithm.
        """
        return len(self.passes)

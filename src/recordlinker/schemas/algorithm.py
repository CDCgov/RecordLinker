"""
recordlinker.schemas.algorithm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the schema definitions for the algorithm records.
These are used for parsing and validating algorithm configurations.
"""

import typing

import pydantic

from recordlinker.linking import matchers
from recordlinker.models.mpi import BlockingKey
from recordlinker.schemas.pii import Feature
from recordlinker.utils import functools as utils


class AlgorithmPass(pydantic.BaseModel):
    """
    The schema for an algorithm pass record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    blocking_keys: list[str]
    evaluators: dict[str, str]
    rule: str
    belongingness_ratio: tuple[float, float]
    kwargs: dict[str, typing.Any] = {}

    @pydantic.field_validator("blocking_keys", mode="before")
    def validate_blocking_keys(cls, value):
        """
        Validate the blocking keys into a list of blocking keys.
        """
        for k in value:
            try:
                getattr(BlockingKey, k)
            except AttributeError:
                raise ValueError(f"Invalid blocking key: {k}")
        return value

    @pydantic.field_validator("evaluators", mode="before")
    def validate_evaluators(cls, value):
        """
        Validate the evaluators into a list of feature comparison functions.
        """
        for k, v in value.items():
            try:
                getattr(Feature, k)
            except AttributeError:
                raise ValueError(f"Invalid feature: {k}")
            func = utils.str_to_callable(v)
            # Ensure the function is a valid feature comparison function
            if not utils.check_signature(func, matchers.FEATURE_COMPARE_FUNC):
                raise ValueError(f"Invalid evaluator: {v}")
        return value

    @pydantic.field_validator("rule", mode="before")
    def validate_rule(cls, value):
        """
        Validate the rule into a match rule function.
        """
        func = utils.str_to_callable(value)
        if not utils.check_signature(func, matchers.MATCH_RULE_FUNC):
            raise ValueError(f"Invalid matching rule: {value}")
        return value

    @pydantic.field_validator("belongingness_ratio", mode="before")
    def validate_belongingness_ratio(cls, value):
        """
        Validate the Belongingness Ratio Threshold Range.
        """
        lower_bound, upper_bound = value
        if lower_bound < 0 or lower_bound > 1:
            raise ValueError(f"Invalid lower bound: {lower_bound}")
        if upper_bound < 0 or upper_bound > 1:
            raise ValueError(f"Invalid upper bound: {upper_bound}")
        if lower_bound > upper_bound:
            raise ValueError(f"Invalid range. Lower bound must be less than upper bound: {value}")
        return (lower_bound, upper_bound)


class Algorithm(pydantic.BaseModel):
    """
    The schema for an algorithm record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    label: str = pydantic.Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: typing.Optional[str] = None
    is_default: bool = False
    include_multiple_matches: bool = True
    passes: typing.Sequence[AlgorithmPass]


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

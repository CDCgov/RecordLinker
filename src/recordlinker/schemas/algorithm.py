"""
recordlinker.schemas.algorithm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the schema definitions for the algorithm records.
These are used for parsing and validating algorithm configurations.
"""

import typing

import pydantic

from recordlinker import utils
from recordlinker.linking import matchers
from recordlinker.models.mpi import BlockingKey
from recordlinker.schemas.pii import Feature


class AlgorithmPass(pydantic.BaseModel):
    """
    The schema for an algorithm pass record.
    """
    model_config = pydantic.ConfigDict(from_attributes=True)

    blocking_keys: list[str]
    evaluators: dict[str, str]
    rule: str
    cluster_ratio: float
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
        Validated the evaluators into a list of feature comparison functions.
        """
        for k, v in value.items():
            try:
                getattr(Feature, k)
            except AttributeError:
                raise ValueError(f"Invalid feature: {k}")
            try:
                func = utils.str_to_callable(v)
                # Ensure the function is a valid feature comparison function
                if not utils.check_signature(func, matchers.FEATURE_COMPARE_FUNC):
                    raise ValueError(f"Invalid evaluator: {v}")
            # Catch an import error if the function cannot be imported
            except ImportError:
                raise ValueError(f"Invalid evaluator: {v}")
        return value

    @pydantic.field_validator("rule", mode="before")
    def validate_rule(cls, value):
        """
        Validate the rule into a match rule function.
        """
        try:
            func = utils.str_to_callable(value)
            if not utils.check_signature(func, matchers.MATCH_RULE_FUNC):
                raise ValueError(f"Invalid matching rule: {value}")
            return value
        except ImportError:
            raise ValueError(f"Invalid matching rule: {value}")


class Algorithm(pydantic.BaseModel):
    """
    The schema for an algorithm record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    label: str = pydantic.Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: typing.Optional[str] = None
    is_default: bool = False
    passes: typing.Sequence[AlgorithmPass]


class AlgorithmSummary(Algorithm):
    """
    The schema for a summary of an algorithm record.
    """

    passes: typing.Sequence[AlgorithmPass] = pydantic.Field(exclude=True)

    # mypy doesn't support decorators on properties; https://github.com/python/mypy/issues/1362
    @pydantic.computed_field # type: ignore[misc]
    @property
    def pass_count(self) -> int:
        """
        Get the number of passes in the algorithm.
        """
        return len(self.passes)

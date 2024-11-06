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

BlockingKeys = typing.Literal[tuple(k.name for k in BlockingKey)]
Features = typing.Literal[tuple(f.name for f in Feature)]
FeatureFuncs = typing.Literal[tuple(f.__name__ for f in matchers.get_feature_functions())]
RuleFuncs = typing.Literal[tuple(f.__name__ for f in matchers.get_rule_functions())]

class Evaluator(pydantic.BaseModel):
    """
    The schema for an evaluator record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    feature: Features
    func: FeatureFuncs

    @pydantic.validator("func", pre=True)
    def validate_func(cls, value):
        """
        Validate the function into a feature comparison function.
        """
        func = utils.str_to_callable(value)
        if not utils.check_signature(func, matchers.FEATURE_COMPARE_FUNC):
            raise ValueError(f"Invalid evaluator: {value}")
        return value


class AlgorithmPass(pydantic.BaseModel):
    """
    The schema for an algorithm pass record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    blocking_keys: list[BlockingKeys]
    evaluators: list[Evaluator]
    rule: RuleFuncs
    cluster_ratio: pydantic.confloat(ge=0, le=1)
    kwargs: dict[str, typing.Any] = {}

    @pydantic.field_validator("rule", mode="before")
    def validate_rule(cls, value):
        """
        Validate the rule into a match rule function.
        """
        func = utils.str_to_callable(value)
        if not utils.check_signature(func, matchers.MATCH_RULE_FUNC):
            raise ValueError(f"Invalid matching rule: {value}")
        return value


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
    @pydantic.computed_field  # type: ignore[misc]
    @property
    def pass_count(self) -> int:
        """
        Get the number of passes in the algorithm.
        """
        return len(self.passes)

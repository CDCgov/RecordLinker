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

BlockingKeys = typing.Literal[tuple(k.name for k in BlockingKey)]
Features = typing.Literal[tuple(f.name for f in Feature)]
FeatureFuncs = typing.Literal[tuple(f for f in matchers.get_feature_func_names())]
RuleFuncs = typing.Literal[tuple(f for f in matchers.get_rule_func_names())]

class Evaluator(pydantic.BaseModel):
    """
    The schema for an evaluator record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True)

    feature: Features
    func: FeatureFuncs


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

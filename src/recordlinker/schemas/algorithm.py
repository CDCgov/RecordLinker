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

    feature: Feature
    func: matchers.FeatureFunc


class AlgorithmPass(pydantic.BaseModel):
    """
    The schema for an algorithm pass record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True, use_enum_values=True)

    blocking_keys: list[BlockingKey]
    evaluators: list[Evaluator]
    rule: matchers.RuleFunc
    cluster_ratio: Annotated[float, pydantic.Field(ge=0, le=1)]
    kwargs: dict[str, typing.Any] = {}


class Algorithm(pydantic.BaseModel):
    """
    The schema for an algorithm record.
    """

    model_config = pydantic.ConfigDict(from_attributes=True, use_enum_values=True)

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

"""
recordlinker.schemas.tuning
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the schema definitions for the tuning jobs.
"""

import datetime
import typing
import uuid

import pydantic
from typing_extensions import Annotated

from recordlinker import models
from recordlinker.utils.datetime import now_utc_no_ms

from .algorithm import LogOdd


class TuningParams(pydantic.BaseModel):
    true_match_pairs: Annotated[int, pydantic.Field(gt=0)] = pydantic.Field(
        description="The number of true match pairs to use for training."
    )
    non_match_pairs: Annotated[int, pydantic.Field(gt=0)] = pydantic.Field(
        description="The number of non-match pairs to use for training."
    )


class TuningResults(pydantic.BaseModel):
    dataset_size: Annotated[int, pydantic.Field(ge=0)] = pydantic.Field(
        default=0, description="The number of records analyzed."
    )
    true_matches_found: Annotated[int, pydantic.Field(ge=0)] = pydantic.Field(
        default=0, description="The number of true matches found."
    )
    non_matches_found: Annotated[int, pydantic.Field(ge=0)] = pydantic.Field(
        default=0, description="The number of non-matches found."
    )
    log_odds: typing.Sequence[LogOdd] = []
    details: str = pydantic.Field(
        default="", description="Additional information about the tuning job."
    )


class TuningJob(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: uuid.UUID = pydantic.Field(default_factory=uuid.uuid4)
    status: models.TuningStatus = pydantic.Field(default=models.TuningStatus.PENDING)
    params: TuningParams
    results: typing.Optional[TuningResults] = None
    started_at: datetime.datetime = pydantic.Field(default_factory=now_utc_no_ms)
    finished_at: typing.Optional[datetime.datetime] = None


class TuningJobResponse(TuningJob):
    status_url: pydantic.HttpUrl

"""
recordlinker.schemas.tuning
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the schema definitions for the tuning jobs.
"""

import dataclasses
import datetime
import typing
import uuid

import fastapi
import pydantic
from typing_extensions import Annotated

from recordlinker import models
from recordlinker.utils.datetime import now_utc_no_ms

from .algorithm import LogOdd
from .pii import Feature
from .pii import PIIRecord


class TuningParams(pydantic.BaseModel):
    true_match_pairs_requested: Annotated[int, pydantic.Field(gt=0)] = pydantic.Field(
        description="The number of true match pairs to use for training.",
    )
    non_match_pairs_requested: Annotated[int, pydantic.Field(gt=0)] = pydantic.Field(
        description="The number of non-match pairs to use for training.",
    )
    non_match_sample_requested: Annotated[int, pydantic.Field(gt=0)] = pydantic.Field(
        description="The number of records to sample for non-match pairs.",
    )


class PassRecommendation(pydantic.BaseModel):
    algorithm_label: str = pydantic.Field(
        description="The name of the algorithm this pass is associated with."
    )
    pass_label: str = pydantic.Field(
        description="The label of the pass within the associated algorithm for which "
        "this recommendation applies."
    )
    recommended_match_window: tuple[
        Annotated[float, pydantic.Field(ge=0, le=1)], Annotated[float, pydantic.Field(ge=0, le=1)]
    ] = pydantic.Field(
        ...,
        description=(
            "A range of decimal values consisting of two endpoint thresholds: a Minimum "
            "Match Threshold—representing an RMS value below which a candidate record is "
            "labeled 'certainly-not' a match—and a Certain Match Threshold, an RMS value "
            "above which a candidate record is labeled a 'certain' match."
        ),
    )


class TuningResults(pydantic.BaseModel):
    true_match_pairs_used: Annotated[int, pydantic.Field(ge=0)] = pydantic.Field(
        default=0, description="The number of true matches found."
    )
    non_match_pairs_used: Annotated[int, pydantic.Field(ge=0)] = pydantic.Field(
        default=0, description="The number of non-matches found."
    )
    non_match_sample_used: Annotated[int, pydantic.Field(ge=0)] = pydantic.Field(
        default=0, description="The number of records sampled for non-matches."
    )
    log_odds: typing.Sequence[LogOdd] = []
    passes: typing.Sequence[PassRecommendation] = []
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

    @classmethod
    def from_tuning_job(cls, job: TuningJob, request: fastapi.Request) -> typing.Self:
        """
        Convenience method to create a TuningJobResponse from a TuningJob
        """
        url: str = str(request.url_for("get-tuning-job", job_id=job.id))
        return cls(**job.model_dump(), status_url=pydantic.HttpUrl(url))


@dataclasses.dataclass
class TuningPair:
    """
    A pair of PIIRecords that are used for training a model.
    """
    record1: PIIRecord
    record2: PIIRecord
    sample_used: typing.Optional[int] = None  # the number of records sampled from to produce the pair

    @classmethod
    def from_data(cls, record1: dict, record2: dict, sample_used: int | None = None) -> typing.Self:
        """
        Contruct a TuningPair from raw PII data dictionaries.
        """
        return cls(
            record1=PIIRecord.from_data(record1),
            record2=PIIRecord.from_data(record2),
            sample_used=sample_used,
        )


@dataclasses.dataclass
class TuningProbabilities:
    """
    A dict of feature specific probabilities that two records are likely to belong to
    the same cluster given a collection of TuningPairs. Also included are the number,
    count, of TuningPairs analyzed and an optional parameter for sample size used.
    """
    probs: dict[Feature, float]  # the feature specific probabilities
    count: int  # the number of pairs analyzed
    sample_used: typing.Optional[int] = None  # the number of records sampled from to produce the probabilities

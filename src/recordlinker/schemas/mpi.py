import typing
import uuid

import pydantic

from .pii import PIIRecord


class PersonRef(pydantic.BaseModel):
    person_reference_id: uuid.UUID
    external_person_id: str | None = None


class PersonRefs(pydantic.BaseModel):
    person_reference_ids: list[uuid.UUID] = pydantic.Field(..., min_length=1)


class PatientRef(pydantic.BaseModel):
    patient_reference_id: uuid.UUID
    external_patient_id: str | None = None


class PatientPersonRef(pydantic.BaseModel):
    patient_reference_id: uuid.UUID
    person_reference_id: uuid.UUID


class PatientRefs(pydantic.BaseModel):
    patients: list[uuid.UUID] = pydantic.Field(..., min_length=1)


class PatientCreatePayload(pydantic.BaseModel):
    person_reference_id: uuid.UUID | None = None
    record: PIIRecord


class PatientUpdatePayload(pydantic.BaseModel):
    person_reference_id: uuid.UUID | None = None
    record: PIIRecord | None = None

    @pydantic.model_validator(mode="after")
    def validate_both_not_empty(self) -> typing.Self:
        """
        Ensure that either person_reference_id or record is not None.
        """
        if self.person_reference_id is None and self.record is None:
            raise ValueError("at least one of person_reference_id or record must be provided")
        return self


class PatientInfo(pydantic.BaseModel):
    patient_reference_id: uuid.UUID
    person_reference_id: uuid.UUID
    record: PIIRecord
    external_patient_id: str | None = None
    external_person_id: str | None = None


class PersonInfo(pydantic.BaseModel):
    person_reference_id: uuid.UUID
    patient_reference_ids: list[uuid.UUID]


class ErrorDetail(pydantic.BaseModel):
    """
    Error detail information.
    """

    loc: list[str]
    msg: str
    type: str


class ErrorResponse(pydantic.BaseModel):
    """

    Error response for MPI operations.
    """

    detail: list[ErrorDetail]


class PaginatedMetaData(pydantic.BaseModel):
    next_cursor: uuid.UUID | None = None
    next: pydantic.HttpUrl | None = None


class PaginatedRefs(pydantic.BaseModel):
    data: list[uuid.UUID] = pydantic.Field(...)
    meta: PaginatedMetaData | None

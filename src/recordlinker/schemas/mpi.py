import typing
import uuid

import pydantic

from .pii import PIIRecord


class PersonRef(pydantic.BaseModel):
    person_reference_id: uuid.UUID
    external_person_id: str | None = None


class PatientRef(pydantic.BaseModel):
    patient_reference_id: uuid.UUID
    external_patient_id: str | None = None


class PatientPersonRef(pydantic.BaseModel):
    patient_reference_id: uuid.UUID
    person_reference_id: uuid.UUID


class PatientCreatePayload(pydantic.BaseModel):
    person_reference_id: uuid.UUID
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

import uuid

import pydantic


class PersonRef(pydantic.BaseModel):
    person_reference_id: uuid.UUID
    external_person_id: str | None = None


class PatientRef(pydantic.BaseModel):
    patient_reference_id: uuid.UUID
    external_patient_id: str | None = None


class PatientPersonRef(pydantic.BaseModel):
    patient_reference_id: uuid.UUID
    person_reference_id: uuid.UUID


class PatientRefs(pydantic.BaseModel):
    patients: list[uuid.UUID] = pydantic.Field(..., min_length=1)

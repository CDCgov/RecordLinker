import uuid

import pydantic


class PersonRef(pydantic.BaseModel):
    person_reference_id: uuid.UUID


class PatientPersonRef(pydantic.BaseModel):
    patient_reference_id: uuid.UUID
    person_reference_id: uuid.UUID

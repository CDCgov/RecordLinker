import uuid

import pydantic


class PersonRef(pydantic.BaseModel):
    person_ref_id: uuid.UUID


class PatientPersonRef(pydantic.BaseModel):
    patient_ref_id: uuid.UUID
    person_ref_id: uuid.UUID

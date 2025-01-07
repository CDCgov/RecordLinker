"""
recordlinker.utils.routes
~~~~~~~~~~~~~~~~~~~~~~~~~

Utility functions for the RecordLinker routers.
"""

import fastapi
import sqlalchemy.orm as orm

from recordlinker import models
from recordlinker import schemas
from recordlinker.database import algorithm_service
from recordlinker.hl7 import fhir


def algorithm_or_422(db_session: orm.Session, label: str | None) -> models.Algorithm:
    """
    Get the Algorithm, or default if no label. Raise a 422 if no Algorithm can be found.
    """
    algorithm = (
        algorithm_service.get_algorithm(db_session, label)
        if label
        else algorithm_service.default_algorithm(db_session)
    )
    if not algorithm:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No algorithm found",
        )
    return algorithm


def fhir_record_or_422(bundle: dict) -> schemas.PIIRecord:
    """
    Extract the patient record from a FHIR bundle. Raise a 422 if no valid Patient resource is found.
    """
    # Now extract the patient record we want to link
    resource: dict = fhir.get_first_patient_resource(bundle)
    if not resource:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Supplied bundle contains no Patient resource",
        )
    try:
        return fhir.fhir_record_to_pii_record(resource)
    except ValueError:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid Patient resource",
        )

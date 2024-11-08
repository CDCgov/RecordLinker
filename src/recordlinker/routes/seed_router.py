"""
recordlinker.routes.seed_router
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the seed router for the RecordLinker API. Exposing
the seed API endpoints.
"""

import fastapi
import sqlalchemy.orm as orm

from recordlinker import models
from recordlinker import schemas
from recordlinker.database import get_session
from recordlinker.linking import mpi_service as service

router = fastapi.APIRouter()


# TODO: test cases
@router.post("", summary="Batch seed records", status_code=fastapi.status.HTTP_201_CREATED)
def batch(
    data: schemas.ClusterGroup, session: orm.Session = fastapi.Depends(get_session)
) -> schemas.PersonGroup:
    """
    Seed a batch of records into the database.  This endpoint can be used to initialize the MPI
    with existing Person clusters.  The endpoint accepts a list of clusters, such that each cluster
    represents a Person and contains a list of patient records associated with that Person.  This
    endpoint will create a new Person record for each cluster and create a new Patient records for
    each patient in the cluster.

    The endpoint will return a list of Person objects, each containing a person_reference_id and a
    list of Patient objects, each containing patient_reference_ids.

    NOTE: The maximum number of clusters that can be seeded in a single request is 100.
    """
    # check if engine is mysql, if so raise a not supported error
    if session.get_bind().dialect.name == "mysql":
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Batch seeding is not supported for MySQL",
        )

    results: list[schemas.PersonCluster] = []

    for cluster in data.clusters:
        person = models.Person()
        patients = service.bulk_insert_patients(
            session,
            cluster.records,
            person=person,
            external_person_id=cluster.external_person_id,
            commit=False,
        )

        results.append(
            schemas.PersonCluster(
                person_reference_id=person.reference_id,
                external_person_id=cluster.external_person_id,
                patients=[
                    schemas.PatientRef(
                        patient_reference_id=p.reference_id,
                        external_patient_id=p.external_patient_id,
                    )
                    for p in patients
                ],
            )
        )

    return schemas.PersonGroup(persons=results)


# TODO: test cases
@router.delete(
    "", summary="Reset the MPI database", status_code=fastapi.status.HTTP_204_NO_CONTENT
)
def reset(session: orm.Session = fastapi.Depends(get_session)):
    """
    Reset the MPI database by deleting all Person and Patient records.
    """
    service.reset_mpi(session)
    return fastapi.Response(status_code=fastapi.status.HTTP_204_NO_CONTENT)

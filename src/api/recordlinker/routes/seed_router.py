"""
recordlinker.routes.seed_router
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the seed router for the RecordLinker API. Exposing
the seed API endpoints.
"""

import typing

import fastapi
import sqlalchemy.orm as orm

from recordlinker import models
from recordlinker import schemas
from recordlinker.database import get_session
from recordlinker.database import mpi_service as service

router = fastapi.APIRouter()


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

    NOTE: MySQL does not support bulk insert, so when using this dialect, each patient record will
    be inserted individually.  This will be slower than using a dialect that supports bulk insert.

    NOTE: The maximum number of clusters that can be seeded in a single request is 100.
    """
    results: list[schemas.PersonCluster] = []
    dialect = session.get_bind().dialect.name

    for cluster in data.clusters:
        person = models.Person()
        patients: typing.Sequence[models.Patient] = []
        if dialect == "mysql":
            # MySQL does not support bulk insert, so we need to insert each patient individually
            patients = [
                service.insert_patient(
                    session,
                    r,
                    person,
                    external_patient_id=r.external_id,
                    external_person_id=cluster.external_person_id,
                    commit=False,
                )
                for r in cluster.records
            ]
        else:
            patients = service.bulk_insert_patients(
                session,
                cluster.records,
                person,
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


@router.delete("", summary="Reset the MPI database", status_code=fastapi.status.HTTP_204_NO_CONTENT)
def reset(session: orm.Session = fastapi.Depends(get_session)):
    """
    Reset the MPI database by deleting all Person and Patient records.
    """
    service.reset_mpi(session)
    return fastapi.Response(status_code=fastapi.status.HTTP_204_NO_CONTENT)

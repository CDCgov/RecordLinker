import uuid

import pydantic

from recordlinker.schemas.mpi import PatientRef
from recordlinker.schemas.pii import PIIRecord

CLUSTER_MAX_SIZE = 100
# NOTE: the number of records in each cluster can vary, but assuming we have
# less than ~25 records per person, we should be able to fit 100 persons in a
# 1MB request.  This is a reasonable limit for a single request.


class Cluster(pydantic.BaseModel):
    records: list[PIIRecord]
    external_person_id: str | None = None


class ClusterGroup(pydantic.BaseModel):
    clusters: list[Cluster]

    @pydantic.field_validator("clusters", mode="before")
    def validate_clusters(cls, clusters):
        """
        Validate that the clusters are not empty and do not exceed the maximum size.
        """
        if not clusters:
            raise ValueError("Clusters must not be empty")
        if len(clusters) > CLUSTER_MAX_SIZE:
            raise ValueError(f"Clusters must not exceed {CLUSTER_MAX_SIZE} records")
        return clusters


class PersonCluster(pydantic.BaseModel):
    person_reference_id: uuid.UUID
    external_person_id: str | None = None
    patients: list[PatientRef]


class PersonGroup(pydantic.BaseModel):
    persons: list[PersonCluster]

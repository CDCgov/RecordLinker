"""
recordlinker.linking.algorithm_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides the data access functions to the algorithm config tables
"""

import typing

from sqlalchemy import delete
from sqlalchemy import orm
from sqlalchemy import select

from recordlinker import models
from recordlinker import schemas


def list_algorithms(session: orm.Session) -> typing.Sequence[models.Algorithm]:
    """
    List all algorithms from the MPI database.

    :param session: The database session
    :returns: list of all algorithms
    """
    return session.scalars(select(models.Algorithm)).all()


def default_algorithm(session: orm.Session) -> models.Algorithm | None:
    """
    Get the default algorithm from the MPI database.

    :param session: The database session
    :returns: default algorithm
    """
    query = select(models.Algorithm).where(models.Algorithm.is_default == True)  # noqa: E712
    res = session.scalars(query).all()
    if not res:
        return None
    assert len(res) == 1, "Multiple default algorithms found in the database."
    return res[0]


def get_algorithm(session: orm.Session, label: str) -> models.Algorithm | None:
    """
    Get an algorithm by its label from the MPI database.

    :param session: The database session
    :param label: The algorithm label
    :returns: algorithm
    """
    query = select(models.Algorithm).where(models.Algorithm.label == label)
    res = session.scalars(query).all()
    if res:
        assert len(res) == 1, "Multiple algorithms found with the same label."
        return res[0]
    return None


def load_algorithm(
    session: orm.Session,
    data: schemas.Algorithm,
    obj: models.Algorithm | None = None,
    commit: bool = False,
) -> tuple[models.Algorithm, bool]:
    """
    Adds or updates an algorithm in the database

    :param session: The database session
    :param data: The algorithm data
    :param obj: The existing algorithm object or None
    :param commit: Commit the transaction
    :returns: The algorithm object and a boolean indicating if it was created
    """
    algo = data.model_dump()
    passes = algo.pop("passes")
    # use the existing Algorithm or create a new one
    created = obj is None
    obj = obj or models.Algorithm()
    # Create and add the Algorithm
    for key, value in algo.items():
        setattr(obj, key, value)
    if created:
        session.add(obj)
    # Delete the existing AlgorithmPasses
    session.execute(delete(models.AlgorithmPass).where(models.AlgorithmPass.algorithm_id == obj.id))
    # Create and add the AlgorithmPasses
    session.add_all([models.AlgorithmPass(**p, algorithm=obj) for p in passes])

    if commit:
        session.commit()
    return obj, created


def delete_algorithm(session: orm.Session, obj: models.Algorithm, commit: bool = False) -> None:
    """
    Deletes an algorithm from the database

    :param session: The database session
    :param obj: The algorithm to delete
    :param commit: Commit the transaction
    """
    session.delete(obj)
    if commit:
        session.commit()


def clear_algorithms(session: orm.Session, commit: bool = False) -> None:
    """
    Purge all algorithms from the database

    :param session: The database session
    :param commit: Commit the transaction
    """
    session.execute(delete(models.AlgorithmPass))
    session.execute(delete(models.Algorithm))
    if commit:
        session.commit()

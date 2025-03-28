"""
recordlinker.routes.algorithm_router
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the algorithm router for the RecordLinker API. Exposing
the algorithm configuration API endpoints.
"""

import typing

import fastapi
import sqlalchemy.orm as orm

from recordlinker import schemas
from recordlinker.database import algorithm_service as service
from recordlinker.database import get_session

router = fastapi.APIRouter()


@router.get("", status_code=fastapi.status.HTTP_200_OK)
def list_algorithms(
    session: orm.Session = fastapi.Depends(get_session),
) -> typing.Sequence[schemas.AlgorithmSummary]:
    """
    List all algorithms from the MPI database.

    :returns: list of all algorithms
    """
    return [schemas.AlgorithmSummary.model_validate(a) for a in service.list_algorithms(session)]


@router.get("/{label}", status_code=fastapi.status.HTTP_200_OK)
def get_algorithm(
    label: str,
    session: orm.Session = fastapi.Depends(get_session),
) -> schemas.Algorithm:
    """
    Get an algorithm by its label from the MPI database.

    :param label: The algorithm label
    :returns: algorithm
    """
    obj = service.get_algorithm(session, label)
    if obj is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)
    return schemas.Algorithm.model_validate(obj)


@router.post("", status_code=fastapi.status.HTTP_201_CREATED)
def create_algorithm(
    data: schemas.Algorithm, session: orm.Session = fastapi.Depends(get_session)
) -> schemas.Algorithm:
    """
    Create a new algorithm in the MPI database.

    :param data: The algorithm data
    :returns: The created algorithm
    """
    try:
        service.load_algorithm(session, data)
    except ValueError as exc:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    return data


@router.put("/{label}", status_code=fastapi.status.HTTP_200_OK)
def update_algorithm(
    label: str, data: schemas.Algorithm, session: orm.Session = fastapi.Depends(get_session)
) -> schemas.Algorithm:
    """
    Update an existing algorithm in the MPI database.

    :param label: The algorithm label
    :param data: The algorithm data
    :returns: The updated algorithm
    """
    obj = service.get_algorithm(session, label)
    if obj is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)
    try:
        service.load_algorithm(session, data, obj)
    except ValueError as exc:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    return data


@router.delete("/{label}", status_code=fastapi.status.HTTP_204_NO_CONTENT)
def delete_algorithm(label: str, session: orm.Session = fastapi.Depends(get_session)) -> None:
    """
    Delete an algorithm from the MPI database.

    :param label: The algorithm label
    """
    obj = service.get_algorithm(session, label)
    if obj is None:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_404_NOT_FOUND)
    return service.delete_algorithm(session, obj)

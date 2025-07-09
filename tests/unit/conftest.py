import contextlib
import functools
import gzip
import json
import os
import pathlib

import pytest
import sqlalchemy
import sqlalchemy.event
from fastapi.testclient import TestClient

from recordlinker import database
from recordlinker import main
from recordlinker import schemas
from recordlinker.utils import path as utils


def load_test_json_asset(*paths: str) -> dict | list:
    """
    Loads a JSON file from the testing 'assets' directory. Works with both
    regular and gzipped JSON files.
    """
    cwd = pathlib.Path(__file__).resolve().parent
    filename = pathlib.Path(cwd, "assets", *paths)
    func = gzip.open if filename.suffix == ".gz" else open
    with func(filename, "rt") as fobj:
        return json.load(fobj)


@functools.lru_cache
def db_dialect():
    with database.get_test_session() as session:
        return session.get_bind().dialect.name


@pytest.fixture(scope="function")
def session():
    with database.get_test_session() as session:
        yield session


@pytest.fixture(scope="function")
def client():
    # Create a new testing session, its important just to call the
    # get_test_session() function once per test, as it resets the database
    # tables everytime its called
    with database.get_test_session() as session:
        # Override the get_session dependency in the FastAPI app to use
        # a simple function that returns the testing session, this will
        # make the session persist for each call to the client within the
        # scope of the test
        main.app.dependency_overrides[database.get_session] = lambda: session
        with TestClient(main.app, raise_server_exceptions=False) as c:
            c.session = session
            yield c


@pytest.fixture(scope="session", autouse=True)
def clean_test_database():
    """Fixture to clean up the sqlite test database file after the test suite."""
    db_file = None
    with database.get_test_session() as session:
        # test if session is sqlite
        if session.get_bind().dialect.name == "sqlite":
            db_file = session.get_bind().url.database
    # Yield control to the test suite
    yield
    # Cleanup logic: remove the database file if it exists
    if db_file and os.path.exists(db_file):
        os.remove(db_file)


@pytest.fixture(scope="session")
def default_algorithm():
    for algo in utils.read_json("assets/initial_algorithms.json"):
        if algo["label"] == "dibbs-default":
            return schemas.Algorithm.model_validate(algo)


@contextlib.contextmanager
def count_queries(session):
    """
    Context manager that counts the number of queries executed within the scope.

    Usage:
    ```
    with count_queries(session) as count:
      session.query(...).all()
    assert count() == 1
    ```
    """
    query_count = 0

    def _count(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1

    # Attach the event listener
    sqlalchemy.event.listen(sqlalchemy.Engine, "before_cursor_execute", _count)

    try:
        yield lambda: query_count
    finally:
        # Remove the event listener
        sqlalchemy.event.remove(sqlalchemy.Engine, "before_cursor_execute", _count)

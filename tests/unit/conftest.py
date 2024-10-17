import functools
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from recordlinker import database
from recordlinker import main
from recordlinker import models


def load_json_asset(*paths: str) -> dict | list:
    """
    Loads a JSON file from the testing 'assets' directory.
    """
    cwd = pathlib.Path(__file__).resolve().parent
    filename = pathlib.Path(cwd, "assets", *paths)
    with open(filename, "r") as fobj:
        return json.load(fobj)


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
        with TestClient(main.app) as c:
            c.session = session
            yield c


@functools.lru_cache
@pytest.fixture
def basic_algorithm():
    for algo in load_json_asset("default_algorithms.json"):
        if algo["label"] == "dibbs-basic":
            return models.Algorithm.from_dict(**algo)


@functools.lru_cache
@pytest.fixture
def enhanced_algorithm():
    for algo in load_json_asset("default_algorithms.json"):
        if algo["label"] == "dibbs-enhanced":
            return models.Algorithm.from_dict(**algo)

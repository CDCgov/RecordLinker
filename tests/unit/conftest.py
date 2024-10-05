import pytest
from fastapi.testclient import TestClient

from recordlinker import database
from recordlinker import main
from recordlinker import utils


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
            yield c


@pytest.fixture
def basic_algorithm(self):
    return utils.read_json_from_assets("linking", "basic_algorithm.json")["algorithm"]


@pytest.fixture
def enhanced_algorithm(self):
    return utils.read_json_from_assets("linking", "enhanced_algorithm.json")["algorithm"]

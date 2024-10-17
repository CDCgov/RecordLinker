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


@pytest.fixture
def basic_algorithm():
    return models.Algorithm(
        label="dibbs-basic",
        is_default=True,
        description="Basic algorithm",
        passes=[
            models.AlgorithmPass(
                blocking_keys=["BIRTHDATE", "MRN", "SEX"],
                evaluators={
                    "FIRST_NAME": "func:recordlinker.linking.matchers.feature_match_fuzzy_string",
                    "LAST_NAME": "func:recordlinker.linking.matchers.feature_match_exact",
                },
                rule="func:recordlinker.linking.matchers.eval_perfect_match",
                cluster_ratio=0.9,
                kwargs={
                    "thresholds": {
                        "FIRST_NAME": 0.9,
                        "LAST_NAME": 0.9,
                        "BIRTHDATE": 0.95,
                        "ADDRESS": 0.9,
                        "CITY": 0.92,
                        "ZIP": 0.95,
                    }
                },
            ),
            models.AlgorithmPass(
                blocking_keys=["ZIP", "FIRST_NAME", "LAST_NAME", "SEX"],
                evaluators={
                    "ADDRESS": "func:recordlinker.linking.matchers.feature_match_fuzzy_string",
                    "BIRTHDATE": "func:recordlinker.linking.matchers.feature_match_exact",
                },
                rule="func:recordlinker.linking.matchers.eval_perfect_match",
                cluster_ratio=0.9,
                kwargs={
                    "thresholds": {
                        "FIRST_NAME": 0.9,
                        "LAST_NAME": 0.9,
                        "BIRTHDATE": 0.95,
                        "ADDRESS": 0.9,
                        "CITY": 0.92,
                        "ZIP": 0.95,
                    }
                },
            )
        ],
    )


@pytest.fixture
def enhanced_algorithm():
    return models.Algorithm(
        label="dibbs-enhanced",
        is_default=False,
        description="Enhanced algorithm",
        passes=[
            models.AlgorithmPass(
                blocking_keys=["BIRTHDATE", "MRN", "SEX"],
                evaluators={
                    "FIRST_NAME": "func:recordlinker.linking.matchers.feature_match_log_odds_fuzzy_compare",
                    "LAST_NAME": "func:recordlinker.linking.matchers.feature_match_log_odds_fuzzy_compare",
                },
                rule="func:recordlinker.linking.matchers.eval_log_odds_cutoff",
                cluster_ratio=0.9,
                kwargs={
                    "similarity_measure": "JaroWinkler",
                    "thresholds": {
                        "FIRST_NAME": 0.9,
                        "LAST_NAME": 0.9,
                        "BIRTHDATE": 0.95,
                        "ADDRESS": 0.9,
                        "CITY": 0.92,
                        "ZIP": 0.95,
                    },
                    "true_match_threshold": 12.2,
                    "log_odds": {
                        "ADDRESS": 8.438284928858774,
                        "BIRTHDATE": 10.126641103800338,
                        "CITY": 2.438553006137189,
                        "FIRST_NAME": 6.849475906891162,
                        "LAST_NAME": 6.350720397426025,
                        "MRN": 0.3051262572525359,
                        "SEX": 0.7510419059643679,
                        "STATE": 0.022376768992488694,
                        "ZIP": 4.975031471124867,
                    },
                },
            ),
            models.AlgorithmPass(
                blocking_keys=["ZIP", "FIRST_NAME", "LAST_NAME", "SEX"],
                evaluators={
                    "ADDRESS": "func:recordlinker.linking.matchers.feature_match_log_odds_fuzzy_compare",
                    "BIRTHDATE": "func:recordlinker.linking.matchers.feature_match_log_odds_fuzzy_compare",
                },
                rule="func:recordlinker.linking.matchers.eval_log_odds_cutoff",
                cluster_ratio=0.9,
                kwargs={
                    "similarity_measure": "JaroWinkler",
                    "thresholds": {
                        "FIRST_NAME": 0.9,
                        "LAST_NAME": 0.9,
                        "BIRTHDATE": 0.95,
                        "ADDRESS": 0.9,
                        "CITY": 0.92,
                        "ZIP": 0.95,
                    },
                    "true_match_threshold": 17.0,
                    "log_odds": {
                        "ADDRESS": 8.438284928858774,
                        "BIRTHDATE": 10.126641103800338,
                        "CITY": 2.438553006137189,
                        "FIRST_NAME": 6.849475906891162,
                        "LAST_NAME": 6.350720397426025,
                        "MRN": 0.3051262572525359,
                        "SEX": 0.7510419059643679,
                        "STATE": 0.022376768992488694,
                        "ZIP": 4.975031471124867,
                    },
                },
            )
        ],
    )

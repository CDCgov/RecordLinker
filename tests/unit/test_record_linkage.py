# flake8: noqa
# fmt: off
import copy
import json
import os
import pathlib

import pytest
from recordlinker.config import settings
from recordlinker.utils import run_migrations
from recordlinker.utils import _clean_up

from fastapi import status
from fastapi.testclient import TestClient
from recordlinker.main import app
import copy
import json
import pathlib

from sqlalchemy import create_engine
from sqlalchemy import orm

from recordlinker import models
from recordlinker.config import settings

# fmt: on
client = TestClient(app)


def load_test_bundle():
    test_bundle = json.load(
        open(
            pathlib.Path(__file__).parent.parent.parent
            / "assets"
            / "patient_bundle_to_link_with_mpi.json"
        )
    )
    return test_bundle


@pytest.fixture(autouse=True)
def setup_and_clean_tests():
    # This code will always run before every test in this file
    # We want it to set up env variables and run migrations
    run_migrations()

    # pytest will automatically plug each test in this scoped file
    # in place of this yield
    yield

    # This code will run at the end of the test plugged into the yield
    _clean_up()

@pytest.fixture(scope="function")
def session():
    engine = create_engine(settings.test_db_uri)
    models.Base.metadata.create_all(engine)

    # Create a new session factory and scoped session
    Session = orm.scoped_session(orm.sessionmaker(bind=engine))
    session = Session()

    yield session  # This is where the testing happens

    session.close()  # Cleanup after test
    models.Base.metadata.drop_all(engine)  # Drop all tables after the test

def test_health_check():
    actual_response = client.get("/")
    assert actual_response.status_code == 200
    assert actual_response.json() == {"status": "OK", "mpi_connection_status": "OK"}


def test_openapi():
    actual_response = client.get("/openapi.json")
    assert actual_response.status_code == 200

def test_get_algorithms():
    actual_response = client.get("/algorithms")
    
    assert actual_response.json() == {"algorithms": ["DIBBS_BASIC", "DIBBS_ENHANCED"]}
    assert actual_response.status_code == status.HTTP_200_OK


def test_linkage_bundle_with_no_patient():
    bad_bundle = {"entry": []}
    expected_response = {
        "message": "Supplied bundle contains no Patient resource to link on.",
        "found_match": False,
        "updated_bundle": bad_bundle,
    }
    actual_response = client.post(
        "/link-record",
        json={"bundle": bad_bundle},
    )
    assert actual_response.json() == expected_response
    assert actual_response.status_code == status.HTTP_400_BAD_REQUEST


def test_linkage_invalid_db_type(monkeypatch):
    # temporarily set the db_uri to an invalid value using a with block
    with monkeypatch.context() as m:
        invalid_db_uri = "sqlite:///test.db"
        m.setattr(settings, "db_uri", invalid_db_uri)

        test_bundle = load_test_bundle()

        expected_response = {
            "message": f"Unsupported database {invalid_db_uri} supplied. "
            + "Make sure your environment variables include an entry "
            + "for `mpi_db_type` and that it is set to 'postgres'.",
            "found_match": False,
            "updated_bundle": test_bundle,
        }
        actual_response = client.post("/link-record", json={"bundle": test_bundle})
        assert actual_response.json() == expected_response
        assert actual_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_linkage_success():
    test_bundle = load_test_bundle()
    entry_list = copy.deepcopy(test_bundle["entry"])

    bundle_1 = test_bundle
    bundle_1["entry"] = [entry_list[0]]
    resp_1 = client.post("/link-record", json={"bundle": bundle_1})
    new_bundle = resp_1.json()["updated_bundle"]
    person_1 = [
        r.get("resource")
        for r in new_bundle["entry"]
        if r.get("resource").get("resourceType") == "Person"
    ][0]
    assert not resp_1.json()["found_match"]

    bundle_2 = test_bundle
    bundle_2["entry"] = [entry_list[1]]
    resp_2 = client.post("/link-record", json={"bundle": bundle_2})
    new_bundle = resp_2.json()["updated_bundle"]
    person_2 = [
        r.get("resource")
        for r in new_bundle["entry"]
        if r.get("resource").get("resourceType") == "Person"
    ][0]
    assert resp_2.json()["found_match"]
    assert person_2.get("id") == person_1.get("id")

    bundle_3 = test_bundle
    bundle_3["entry"] = [entry_list[2]]
    resp_3 = client.post("/link-record", json={"bundle": bundle_3})
    assert not resp_3.json()["found_match"]

    # Cluster membership success--justified match
    bundle_4 = test_bundle
    bundle_4["entry"] = [entry_list[3]]
    resp_4 = client.post("/link-record", json={"bundle": bundle_4})
    new_bundle = resp_4.json()["updated_bundle"]
    person_4 = [
        r.get("resource")
        for r in new_bundle["entry"]
        if r.get("resource").get("resourceType") == "Person"
    ][0]
    assert resp_4.json()["found_match"]
    assert person_4.get("id") == person_1.get("id")

    bundle_5 = test_bundle
    bundle_5["entry"] = [entry_list[4]]
    resp_5 = client.post("/link-record", json={"bundle": bundle_5})
    assert not resp_5.json()["found_match"]

    bundle_6 = test_bundle
    bundle_6["entry"] = [entry_list[5]]
    resp_6 = client.post("/link-record", json={"bundle": bundle_6})
    new_bundle = resp_6.json()["updated_bundle"]
    person_6 = [
        r.get("resource")
        for r in new_bundle["entry"]
        if r.get("resource").get("resourceType") == "Person"
    ][0]
    assert not resp_6.json()["found_match"]


def test_use_enhanced_algo():
    test_bundle = load_test_bundle()
    entry_list = copy.deepcopy(test_bundle["entry"])

    bundle_1 = test_bundle
    bundle_1["entry"] = [entry_list[0]]
    resp_1 = client.post(
        "/link-record", json={"bundle": bundle_1, "algorithm": "DIBBS_ENHANCED"}
    )
    new_bundle = resp_1.json()["updated_bundle"]
    person_1 = [
        r.get("resource")
        for r in new_bundle["entry"]
        if r.get("resource").get("resourceType") == "Person"
    ][0]
    assert not resp_1.json()["found_match"]

    bundle_2 = test_bundle
    bundle_2["entry"] = [entry_list[1]]
    resp_2 = client.post(
        "/link-record", json={"bundle": bundle_2, "algorithm": "DIBBS_ENHANCED"}
    )
    new_bundle = resp_2.json()["updated_bundle"]
    person_2 = [
        r.get("resource")
        for r in new_bundle["entry"]
        if r.get("resource").get("resourceType") == "Person"
    ][0]
    assert resp_2.json()["found_match"]
    assert person_2.get("id") == person_1.get("id")

    bundle_3 = test_bundle
    bundle_3["entry"] = [entry_list[2]]
    resp_3 = client.post(
        "/link-record", json={"bundle": bundle_3, "algorithm": "DIBBS_ENHANCED"}
    )
    assert not resp_3.json()["found_match"]

    bundle_4 = test_bundle
    bundle_4["entry"] = [entry_list[3]]
    resp_4 = client.post(
        "/link-record", json={"bundle": bundle_4, "algorithm": "DIBBS_ENHANCED"}
    )
    new_bundle = resp_4.json()["updated_bundle"]
    person_4 = [
        r.get("resource")
        for r in new_bundle["entry"]
        if r.get("resource").get("resourceType") == "Person"
    ][0]
    assert resp_4.json()["found_match"]
    assert person_4.get("id") == person_1.get("id")

    bundle_5 = test_bundle
    bundle_5["entry"] = [entry_list[4]]
    resp_5 = client.post(
        "/link-record", json={"bundle": bundle_5, "algorithm": "DIBBS_ENHANCED"}
    )
    assert not resp_5.json()["found_match"]

    bundle_6 = test_bundle
    bundle_6["entry"] = [entry_list[5]]
    resp_6 = client.post(
        "/link-record", json={"bundle": bundle_6, "algorithm": "DIBBS_ENHANCED"}
    )
    new_bundle = resp_6.json()["updated_bundle"]
    person_6 = [
        r.get("resource")
        for r in new_bundle["entry"]
        if r.get("resource").get("resourceType") == "Person"
    ][0]
    assert not resp_6.json()["found_match"]

def test_invalid_algorithm_param():
    test_bundle = load_test_bundle()
    expected_response = {
                "found_match": False,
                "updated_bundle": test_bundle,
                "message": "Error: Invalid algorithm specified"
            }
    
    actual_response = client.post(
        "/link-record", json={"bundle": test_bundle, "algorithm": "INVALID"}
    )
    
    assert actual_response.json() == expected_response
    assert actual_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

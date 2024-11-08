"""
unit.routes.test_seed_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.routes.seed_router module.
"""
import pytest
from conftest import db_dialect, load_test_json_asset

from recordlinker import models


class TestBatchMySQL:
    @classmethod
    def setup_class(cls):
        if db_dialect() != "mysql":
            pytest.skip("Test skipped because the database dialect is not MySQL")

    def test_mysql_not_supported(self, client, session):
        response = client.post("/seed/batch", json={"clusters": []})
        assert response.status_code == 422
        assert response.json() == {"detail": "Batch seeding is not supported for MySQL"}


class TestBatch:
    @classmethod
    def setup_class(cls):
        if db_dialect() == "mysql":
            pytest.skip("Test skipped because the database dialect is MySQL")

    def test_large_batch(self, client):
        data = load_test_json_asset("seed_test.json.gz")
        response = client.post("/seed/batch", json=data)
        assert response.status_code == 201
        persons = response.json()["persons"]
        assert len(persons) == 100
        assert len(persons[0]["patients"]) == 13
        assert len(persons[99]["patients"]) == 7
        assert sum(len(p["patients"]) for p in persons) == 1285
        assert client.session.query(models.Person).count() == 100
        assert client.session.query(models.Patient).count() == 1285
        assert client.session.query(models.BlockingValue).count() == 8995


class TestReset:
    def test_reset(self, client):
        person = models.Person()
        patient = models.Patient(person=person, data={})
        client.session.add(patient)
        bv = models.BlockingValue(patient=patient, blockingkey=1, value="test")
        client.session.add(bv)
        client.session.flush()

        assert client.session.query(models.Person).count() == 1
        assert client.session.query(models.Patient).count() == 1
        assert client.session.query(models.BlockingValue).count() == 1
        response = client.delete("/seed/reset")
        assert response.status_code == 204
        assert client.session.query(models.Person).count() == 0
        assert client.session.query(models.Patient).count() == 0
        assert client.session.query(models.BlockingValue).count() == 0

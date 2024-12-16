"""
unit.routes.test_seed_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.routes.seed_router module.
"""

import unittest.mock as mock

from conftest import load_test_json_asset

from recordlinker import models


class TestBatch:
    def test_empty_clusters(self, client):
        response = client.post("/seed", json={"clusters": []})
        assert response.status_code == 422
        assert response.json()["detail"][0]["msg"] == "Value error, Clusters must not be empty"

    def test_too_many_clusters(self, client):
        data = {"clusters": [{"records": []} for _ in range(101)]}
        response = client.post("/seed", json=data)
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Value error, Clusters must not exceed 100 records"
        )

    def test_large_batch(self, client):
        data = load_test_json_asset("seed_test.json.gz")
        response = client.post("/seed", json=data)
        assert response.status_code == 201
        persons = response.json()["persons"]
        assert len(persons) == 100
        assert len(persons[0]["patients"]) == 13
        assert len(persons[99]["patients"]) == 7
        assert sum(len(p["patients"]) for p in persons) == 1285
        assert client.session.query(models.Person).count() == 100
        assert client.session.query(models.Patient).count() == 1285
        assert client.session.query(models.BlockingValue).count() == 10280

    @mock.patch("recordlinker.database.algorithm_service.default_algorithm")
    def test_seed_and_link(self, mock_algorithm, basic_algorithm, client):
        mock_algorithm.return_value = basic_algorithm
        record = {
            "birth_date": "1956-09-06",
            "sex": "F",
            "address": [{"line": ["581 Baker Club"], "postal_code": "80373"}],
            "name": [
                {
                    "family": "Cervantes",
                    "given": ["Jason"],
                }
            ],
        }
        seed_resp = client.post("/seed", json={"clusters": [{"records": [record]}]})
        assert seed_resp.status_code == 201
        persons = seed_resp.json()["persons"]
        assert len(persons) == 1
        response = client.post("/link", json={"record": record})
        assert response.status_code == 200


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
        response = client.delete("/seed")
        assert response.status_code == 204
        assert client.session.query(models.Person).count() == 0
        assert client.session.query(models.Patient).count() == 0
        assert client.session.query(models.BlockingValue).count() == 0

"""
unit.routes.test_seed_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.routes.seed_router module.
"""

import unittest.mock as mock

import pytest
from conftest import load_test_json_asset

from recordlinker import models


class TestBatch:
    def path(self, client):
        return client.app.url_path_for("seed-batch")

    def test_empty_clusters(self, client):
        response = client.post(self.path(client), json={"clusters": []})
        assert response.status_code == 422
        assert response.json()["detail"][0]["msg"] == "Value error, Clusters must not be empty"

    def test_too_many_clusters(self, client):
        data = {"clusters": [{"records": []} for _ in range(101)]}
        response = client.post(self.path(client), json=data)
        assert response.status_code == 422
        assert (
            response.json()["detail"][0]["msg"]
            == "Value error, Clusters must not exceed 100 records"
        )

    def test_large_batch(self, client):
        # NOTE: The seed_test.json file was generated with scripts/gen_seed_test_data.py
        # rerun that script and adjust these values if the data format needs to change.
        data = load_test_json_asset("seed_test.json.gz")
        response = client.post(self.path(client), json=data)
        assert response.status_code == 201
        persons = response.json()["persons"]
        assert len(persons) == 100
        assert len(persons[0]["patients"]) == 5
        assert len(persons[99]["patients"]) == 14
        assert sum(len(p["patients"]) for p in persons) == 1397
        assert client.session.query(models.Person).count() == 100
        assert client.session.query(models.Patient).count() == 1397
        assert client.session.query(models.BlockingValue).count() == 12139

    @pytest.fixture
    @mock.patch("recordlinker.database.algorithm_service.default_algorithm")
    def test_seed_and_link(self, mock_algorithm, default_algorithm, client):
        mock_algorithm.return_value = default_algorithm
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
        seed_resp = client.post(self.path(client), json={"clusters": [{"records": [record]}]})
        assert seed_resp.status_code == 201
        persons = seed_resp.json()["persons"]
        assert len(persons) == 1
        link_url = client.app.url_path_for("link-record")
        response = client.post(link_url, json={"record": record})
        assert response.status_code == 200


class TestReset:
    def path(self, client):
        return client.app.url_path_for("seed-reset")

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
        response = client.delete(self.path(client))
        assert response.status_code == 204
        assert client.session.query(models.Person).count() == 0
        assert client.session.query(models.Patient).count() == 0
        assert client.session.query(models.BlockingValue).count() == 0

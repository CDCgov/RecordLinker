"""
unit.routes.test_link_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.routes.link_router module.
"""

import copy
import json
import uuid
from unittest import mock

import pytest
from conftest import load_test_json_asset
from fastapi import HTTPException
from fastapi import status

from recordlinker import models
from recordlinker import schemas
from recordlinker.database import algorithm_service
from recordlinker.hl7 import fhir
from recordlinker.routes import link_router


def test_algorithm_or_422(session):
    algo1 = models.Algorithm(label="default", is_default=True, description="First algorithm")
    session.add(algo1)
    session.commit()

    alg = link_router.algorithm_or_422(session, "default")
    assert alg.label == "default"
    alg = link_router.algorithm_or_422(session, None)
    assert alg.label == "default"
    with pytest.raises(HTTPException) as exc:
        link_router.algorithm_or_422(session, "invalid")
        assert exc.value.status_code == 422


def test_fhir_record_or_422():
    with pytest.raises(HTTPException) as exc:
        link_router.fhir_record_or_422({})
        assert exc.value.status_code == 422
    with pytest.raises(HTTPException) as exc:
        link_router.fhir_record_or_422({"resourceType": "Patient"})
        assert exc.value.status_code == 422
    with pytest.raises(HTTPException) as exc:
        link_router.fhir_record_or_422({"entry": []})
        assert exc.value.status_code == 422
    with pytest.raises(HTTPException) as exc:
        link_router.fhir_record_or_422({"entry": [{"resource": {"resourceType": "Encounter"}}]})
        assert exc.value.status_code == 422
    record = link_router.fhir_record_or_422(
        {"entry": [{"resource": {"resourceType": "Patient", "id": "1"}}]}
    )
    assert record.external_id == "1"


class TestLink:
    def path(self, client):
        return client.app.url_path_for("link-record")

    @pytest.fixture
    def patients(self):
        bundle = load_test_json_asset("simple_patient_bundle_to_link_with_mpi.json")
        patients: list[schemas.PIIRecord] = []
        for entry in bundle["entry"]:
            if entry.get("resource", {}).get("resourceType", {}) == "Patient":
                patients.append(fhir.fhir_record_to_pii_record(entry["resource"]))
        return patients

    @mock.patch("recordlinker.database.algorithm_service.default_algorithm")
    def test_link_success(self, patched_subprocess, default_algorithm, patients, client):
        patched_subprocess.return_value = default_algorithm
        response_1 = client.post(
            self.path(client), json={"record": json.loads(patients[0].model_dump_json(exclude_none=True))}
        )
        person_1 = response_1.json()["person_reference_id"]
        assert response_1.json()["patient_reference_id"] and uuid.UUID(
            response_1.json()["patient_reference_id"]
        )
        assert person_1
        assert response_1.json()["match_grade"] == "certainly-not"
        assert not response_1.json()["results"]

        response_2 = client.post(
            self.path(client), json={"record": json.loads(patients[1].model_dump_json(exclude_none=True))}
        )
        person_2 = response_2.json()["person_reference_id"]
        assert response_2.json()["patient_reference_id"] and uuid.UUID(
            response_2.json()["patient_reference_id"]
        )
        assert person_2 == person_1
        assert response_2.json()["match_grade"] == "certain"
        assert len(response_2.json()["results"]) == 1

        response_3 = client.post(
            self.path(client), json={"record": json.loads(patients[2].model_dump_json(exclude_none=True))}
        )
        person_3 = response_3.json()["person_reference_id"]
        assert response_3.json()["patient_reference_id"] and uuid.UUID(
            response_3.json()["patient_reference_id"]
        )
        assert person_3
        assert response_3.json()["match_grade"] == "certainly-not"
        assert not response_3.json()["results"]

        # Cluster membership success--justified match
        response_4 = client.post(
            self.path(client), json={"record": json.loads(patients[3].model_dump_json(exclude_none=True))}
        )
        person_4 = response_4.json()["person_reference_id"]
        assert response_4.json()["patient_reference_id"] and uuid.UUID(
            response_4.json()["patient_reference_id"]
        )
        assert person_4 == person_1
        assert response_4.json()["match_grade"] == "certain"
        assert len(response_2.json()["results"]) == 1

        response_5 = client.post(
            self.path(client), json={"record": json.loads(patients[4].model_dump_json(exclude_none=True))}
        )
        person_5 = response_5.json()["person_reference_id"]
        assert response_5.json()["patient_reference_id"] and uuid.UUID(
            response_5.json()["patient_reference_id"]
        )
        assert person_5
        assert response_5.json()["match_grade"] == "certainly-not"
        assert not response_3.json()["results"]

        response_6 = client.post(
            self.path(client), json={"record": json.loads(patients[5].model_dump_json(exclude_none=True))}
        )
        person_6 = response_6.json()["person_reference_id"]
        assert response_6.json()["patient_reference_id"] and uuid.UUID(
            response_6.json()["patient_reference_id"]
        )
        assert person_6
        assert response_6.json()["match_grade"] == "certainly-not"
        assert not response_6.json()["results"]

    @mock.patch("recordlinker.database.algorithm_service.get_algorithm")
    def test_link_invalid_algorithm_param(self, patched_subprocess, patients, client):
        patched_subprocess.return_value = None
        actual_response = client.post(
            self.path(client),
            json={
                "record": json.loads(patients[0].model_dump_json(exclude_none=True)),
                "algorithm": "INVALID",
            },
        )

        assert actual_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert actual_response.json()["detail"] == "No algorithm found"

    @mock.patch("recordlinker.database.algorithm_service.default_algorithm")
    def test_link_no_default_algorithm(self, patched_subprocess, patients, client):
        patched_subprocess.return_value = None
        actual_response = client.post(
            self.path(client),
            json={
                "record": json.loads(patients[0].model_dump_json(exclude_none=True)),
                "algorithm": "INVALID",
            },
        )

        assert actual_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert actual_response.json()["detail"] == "No algorithm found"


class TestLinkFHIR:
    def path(self, client):
        return client.app.url_path_for("link-fhir")

    @mock.patch("recordlinker.database.algorithm_service.default_algorithm")
    def test_bundle_with_no_patient(self, patched_subprocess, default_algorithm, client):
        patched_subprocess.return_value = default_algorithm
        bad_bundle = {"entry": []}
        expected_response = {
            "detail": "Supplied bundle contains no Patient resource",
        }
        actual_response = client.post(
            self.path(client),
            json={"bundle": bad_bundle},
        )
        assert actual_response.json() == expected_response
        assert actual_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @mock.patch("recordlinker.database.algorithm_service.default_algorithm")
    def test_invalid_bundle(self, patched_subprocess, default_algorithm, client):
        patched_subprocess.return_value = default_algorithm
        bad_bundle = {"entry": [{"resource": {"resourceType": "Patient", "name": "John Doe"}}]}
        expected_response = {
            "detail": "Invalid Patient resource",
        }
        actual_response = client.post(
            self.path(client),
            json={"bundle": bad_bundle},
        )
        assert actual_response.json() == expected_response
        assert actual_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @mock.patch("recordlinker.database.algorithm_service.default_algorithm")
    def test_success(self, patched_subprocess, default_algorithm, client):
        patched_subprocess.return_value = default_algorithm
        test_bundle = load_test_json_asset("patient_bundle_to_link_with_mpi.json")
        entry_list = copy.deepcopy(test_bundle["entry"])

        bundle_1 = test_bundle
        bundle_1["entry"] = [entry_list[0]]
        resp_1 = client.post(self.path(client), json={"bundle": bundle_1})
        new_bundle = resp_1.json()["updated_bundle"]
        person_1 = [
            r.get("resource")
            for r in new_bundle["entry"]
            if r.get("resource").get("resourceType") == "Person"
        ][0]
        assert resp_1.json()["patient_reference_id"] and uuid.UUID(
            resp_1.json()["patient_reference_id"]
        )
        assert resp_1.json()["person_reference_id"] == person_1.get("id")
        assert resp_1.json()["match_grade"] == "certainly-not"
        assert not resp_1.json()["results"]

        bundle_2 = test_bundle
        bundle_2["entry"] = [entry_list[1]]
        resp_2 = client.post(self.path(client), json={"bundle": bundle_2})
        new_bundle = resp_2.json()["updated_bundle"]
        person_2 = [
            r.get("resource")
            for r in new_bundle["entry"]
            if r.get("resource").get("resourceType") == "Person"
        ][0]
        assert resp_2.json()["patient_reference_id"] and uuid.UUID(
            resp_2.json()["patient_reference_id"]
        )
        assert resp_2.json()["person_reference_id"] == person_1.get("id")
        assert person_2.get("id") == person_1.get("id")
        assert resp_2.json()["match_grade"] == "certain"
        assert len(resp_2.json()["results"]) == 1

        bundle_3 = test_bundle
        bundle_3["entry"] = [entry_list[2]]
        resp_3 = client.post(self.path(client), json={"bundle": bundle_3})
        new_bundle = resp_3.json()["updated_bundle"]
        person_3 = [
            r.get("resource")
            for r in new_bundle["entry"]
            if r.get("resource").get("resourceType") == "Person"
        ][0]
        assert resp_3.json()["patient_reference_id"] and uuid.UUID(
            resp_3.json()["patient_reference_id"]
        )
        assert resp_3.json()["person_reference_id"] == person_3.get("id")
        assert resp_3.json()["match_grade"] == "certainly-not"
        assert not resp_3.json()["results"]

        # Cluster membership success--justified match
        bundle_4 = test_bundle
        bundle_4["entry"] = [entry_list[3]]
        resp_4 = client.post(self.path(client), json={"bundle": bundle_4})
        new_bundle = resp_4.json()["updated_bundle"]
        person_4 = [
            r.get("resource")
            for r in new_bundle["entry"]
            if r.get("resource").get("resourceType") == "Person"
        ][0]
        assert resp_4.json()["patient_reference_id"] and uuid.UUID(
            resp_4.json()["patient_reference_id"]
        )
        assert resp_4.json()["person_reference_id"] == person_4.get("id")
        assert person_4.get("id") == person_1.get("id")
        assert resp_4.json()["match_grade"] == "certain"
        assert len(resp_4.json()["results"]) == 1

        bundle_5 = test_bundle
        bundle_5["entry"] = [entry_list[4]]
        resp_5 = client.post(self.path(client), json={"bundle": bundle_5})
        new_bundle = resp_5.json()["updated_bundle"]
        person_5 = [
            r.get("resource")
            for r in new_bundle["entry"]
            if r.get("resource").get("resourceType") == "Person"
        ][0]
        assert resp_5.json()["patient_reference_id"] and uuid.UUID(
            resp_5.json()["patient_reference_id"]
        )
        assert resp_5.json()["person_reference_id"] == person_5.get("id")
        assert resp_5.json()["match_grade"] == "certainly-not"
        assert not resp_5.json()["results"]

        bundle_6 = test_bundle
        bundle_6["entry"] = [entry_list[5]]
        resp_6 = client.post(self.path(client), json={"bundle": bundle_6})
        new_bundle = resp_6.json()["updated_bundle"]
        person_6 = [
            r.get("resource")
            for r in new_bundle["entry"]
            if r.get("resource").get("resourceType") == "Person"
        ][0]
        assert resp_6.json()["patient_reference_id"] and uuid.UUID(
            resp_6.json()["patient_reference_id"]
        )
        assert resp_6.json()["person_reference_id"] == person_6.get("id")
        assert resp_6.json()["match_grade"] == "certainly-not"
        assert not resp_6.json()["results"]

    @mock.patch("recordlinker.database.algorithm_service.get_algorithm")
    def test_invalid_algorithm_param(self, patched_subprocess, client):
        patched_subprocess.return_value = None
        test_bundle = load_test_json_asset("patient_bundle_to_link_with_mpi.json")
        expected_response = {
            "detail": "No algorithm found",
        }

        actual_response = client.post(
            self.path(client), json={"bundle": test_bundle, "algorithm": "INVALID"}
        )

        assert actual_response.json() == expected_response
        assert actual_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestMatch:
    def path(self, client):
        return client.app.url_path_for("match-record")

    @pytest.fixture
    def patients(self) -> list[schemas.PIIRecord]:
        bundle = load_test_json_asset("simple_patient_bundle_to_link_with_mpi.json")
        patients: list[schemas.PIIRecord] = []
        for entry in bundle["entry"]:
            if entry.get("resource", {}).get("resourceType", {}) == "Patient":
                patients.append(fhir.fhir_record_to_pii_record(entry["resource"]))
        return patients

    def test_invalid_algorithm(self, client):
        resp = client.post(self.path(client), json={"record": {}})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert resp.json()["detail"] == "No algorithm found"

    def test_no_match(self, client, default_algorithm, patients):
        algorithm_service.load_algorithm(client.session, default_algorithm)
        client.session.commit()
        resp = client.post(self.path(client), json={"record": patients[0].to_dict(True)})
        assert resp.status_code == status.HTTP_200_OK
        payload = resp.json()
        assert payload["match_grade"] == "certainly-not"
        assert payload["person_reference_id"] is None
        assert payload["results"] == []
        assert payload.get("patient_reference_id") is None
        assert len(client.session.query(models.Patient).all()) == 0

    def test_match(self, client, default_algorithm, patients):
        algorithm_service.load_algorithm(client.session, default_algorithm)
        client.session.commit()
        per1 = client.post(client.app.url_path_for("link-record"), json={"record": patients[0].to_dict(True)}).json()["person_reference_id"]

        resp = client.post(self.path(client), json={"record": patients[0].to_dict(True)})
        assert resp.status_code == status.HTTP_200_OK
        payload = resp.json()
        assert payload["match_grade"] == "certain"
        assert payload["person_reference_id"] == per1
        assert len(payload["results"]) == 1
        assert payload["results"][0]["person_reference_id"] == per1
        assert payload.get("patient_reference_id") is None
        assert len(client.session.query(models.Patient).all()) == 1


class TestMatchFHIR:
    def path(self, client):
        return client.app.url_path_for("match-fhir")

    @pytest.fixture
    def patient_bundles(self) -> list[dict]:
        bundles: list[dict] = []
        data = load_test_json_asset("simple_patient_bundle_to_link_with_mpi.json")
        for entry in data["entry"]:
            bundles.append({"entry": [entry]})
        return bundles

    def test_invalid_algorithm(self, client):
        resp = client.post(self.path(client), json={"bundle": {}})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert resp.json()["detail"] == "No algorithm found"

    def test_no_match(self, client, default_algorithm, patient_bundles):
        algorithm_service.load_algorithm(client.session, default_algorithm)
        client.session.commit()
        resp = client.post(self.path(client), json={"bundle": patient_bundles[0]})
        assert resp.status_code == status.HTTP_200_OK
        payload = resp.json()
        assert payload["match_grade"] == "certainly-not"
        assert payload["person_reference_id"] is None
        assert payload["results"] == []
        assert payload.get("patient_reference_id") is None
        assert payload["updated_bundle"] is None
        assert len(client.session.query(models.Patient).all()) == 0

    def test_match(self, client, default_algorithm, patient_bundles):
        algorithm_service.load_algorithm(client.session, default_algorithm)
        client.session.commit()
        per1 = client.post(client.app.url_path_for("link-fhir"), json={"bundle": patient_bundles[0]}).json()["person_reference_id"]

        resp = client.post(self.path(client), json={"bundle": patient_bundles[0]})
        assert resp.status_code == status.HTTP_200_OK
        payload = resp.json()
        assert payload["match_grade"] == "certain"
        assert payload["person_reference_id"] == per1
        assert len(payload["results"]) == 1
        assert payload["results"][0]["person_reference_id"] == per1
        assert payload.get("patient_reference_id") is None
        assert len(payload["updated_bundle"]["entry"]) == 2
        assert len(client.session.query(models.Patient).all()) == 1

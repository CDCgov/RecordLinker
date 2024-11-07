"""
unit.routes.test_link_router.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.routes.link_router module.
"""

import copy
import json
from unittest import mock

import pytest
from conftest import load_test_json_asset
from fastapi import status

from recordlinker import schemas
from recordlinker.hl7 import fhir


class TestLinkDIBBS:
    @mock.patch("recordlinker.database.algorithm_service.default_algorithm")
    def test_bundle_with_no_patient(self, patched_subprocess, basic_algorithm, client):
        patched_subprocess.return_value = basic_algorithm
        bad_bundle = {"entry": []}
        expected_response = {
            "detail": "Supplied bundle contains no Patient resource to link on.",
        }
        actual_response = client.post(
            "/link/dibbs",
            json={"bundle": bad_bundle},
        )
        assert actual_response.json() == expected_response
        assert actual_response.status_code == status.HTTP_400_BAD_REQUEST

    @mock.patch("recordlinker.database.algorithm_service.default_algorithm")
    def test_success(self, patched_subprocess, basic_algorithm, client):
        patched_subprocess.return_value = basic_algorithm
        test_bundle = load_test_json_asset("patient_bundle_to_link_with_mpi.json")
        entry_list = copy.deepcopy(test_bundle["entry"])

        bundle_1 = test_bundle
        bundle_1["entry"] = [entry_list[0]]
        resp_1 = client.post("/link/dibbs", json={"bundle": bundle_1})
        new_bundle = resp_1.json()["updated_bundle"]
        person_1 = [
            r.get("resource")
            for r in new_bundle["entry"]
            if r.get("resource").get("resourceType") == "Person"
        ][0]
        assert resp_1.json()["prediction"] == "no_match"

        bundle_2 = test_bundle
        bundle_2["entry"] = [entry_list[1]]
        resp_2 = client.post("/link/dibbs", json={"bundle": bundle_2})
        new_bundle = resp_2.json()["updated_bundle"]
        person_2 = [
            r.get("resource")
            for r in new_bundle["entry"]
            if r.get("resource").get("resourceType") == "Person"
        ][0]
        assert resp_2.json()["prediction"] == "match"
        assert person_2.get("id") == person_1.get("id")

        bundle_3 = test_bundle
        bundle_3["entry"] = [entry_list[2]]
        resp_3 = client.post("/link/dibbs", json={"bundle": bundle_3})
        assert resp_3.json()["prediction"] == "no_match"

        # Cluster membership success--justified match
        bundle_4 = test_bundle
        bundle_4["entry"] = [entry_list[3]]
        resp_4 = client.post("/link/dibbs", json={"bundle": bundle_4})
        new_bundle = resp_4.json()["updated_bundle"]
        person_4 = [
            r.get("resource")
            for r in new_bundle["entry"]
            if r.get("resource").get("resourceType") == "Person"
        ][0]
        assert resp_4.json()["prediction"] == "match"
        assert person_4.get("id") == person_1.get("id")

        bundle_5 = test_bundle
        bundle_5["entry"] = [entry_list[4]]
        resp_5 = client.post("/link/dibbs", json={"bundle": bundle_5})
        assert resp_5.json()["prediction"] == "no_match"

        bundle_6 = test_bundle
        bundle_6["entry"] = [entry_list[5]]
        resp_6 = client.post("/link/dibbs", json={"bundle": bundle_6})
        new_bundle = resp_6.json()["updated_bundle"]
        assert resp_6.json()["prediction"] == "no_match"

    @mock.patch("recordlinker.database.algorithm_service.get_algorithm")
    def test_enhanced_algo(self, patched_subprocess, enhanced_algorithm, client):
        patched_subprocess.return_value = enhanced_algorithm
        test_bundle = load_test_json_asset("patient_bundle_to_link_with_mpi.json")
        entry_list = copy.deepcopy(test_bundle["entry"])

        bundle_1 = test_bundle
        bundle_1["entry"] = [entry_list[0]]
        resp_1 = client.post("/link/dibbs", json={"bundle": bundle_1, "algorithm": "dibbs-enhanced"})
        new_bundle = resp_1.json()["updated_bundle"]
        person_1 = [
            r.get("resource")
            for r in new_bundle["entry"]
            if r.get("resource").get("resourceType") == "Person"
        ][0]
        assert resp_1.json()["prediction"] == "no_match"

        bundle_2 = test_bundle
        bundle_2["entry"] = [entry_list[1]]
        resp_2 = client.post("/link/dibbs", json={"bundle": bundle_2, "algorithm": "dibbs-enhanced"})
        new_bundle = resp_2.json()["updated_bundle"]
        person_2 = [
            r.get("resource")
            for r in new_bundle["entry"]
            if r.get("resource").get("resourceType") == "Person"
        ][0]
        assert resp_2.json()["prediction"] == "match"
        assert person_2.get("id") == person_1.get("id")

        bundle_3 = test_bundle
        bundle_3["entry"] = [entry_list[2]]
        resp_3 = client.post("/link/dibbs", json={"bundle": bundle_3, "algorithm": "dibbs-enhanced"})
        assert resp_3.json()["prediction"] == "no_match"

        bundle_4 = test_bundle
        bundle_4["entry"] = [entry_list[3]]
        resp_4 = client.post("/link/dibbs", json={"bundle": bundle_4, "algorithm": "dibbs-enhanced"})
        new_bundle = resp_4.json()["updated_bundle"]
        person_4 = [
            r.get("resource")
            for r in new_bundle["entry"]
            if r.get("resource").get("resourceType") == "Person"
        ][0]
        assert resp_4.json()["prediction"] == "match"
        assert person_4.get("id") == person_1.get("id")

        bundle_5 = test_bundle
        bundle_5["entry"] = [entry_list[4]]
        resp_5 = client.post("/link/dibbs", json={"bundle": bundle_5, "algorithm": "dibbs-enhanced"})
        assert resp_5.json()["prediction"] == "no_match"

        bundle_6 = test_bundle
        bundle_6["entry"] = [entry_list[5]]
        resp_6 = client.post("/link/dibbs", json={"bundle": bundle_6, "algorithm": "dibbs-enhanced"})
        new_bundle = resp_6.json()["updated_bundle"]
        assert resp_6.json()["prediction"] == "no_match"

    @mock.patch("recordlinker.database.algorithm_service.get_algorithm")
    def test_invalid_algorithm_param(self, patched_subprocess, client):
        patched_subprocess.return_value = None
        test_bundle = load_test_json_asset("patient_bundle_to_link_with_mpi.json")
        expected_response = {
            "detail": "Error: Invalid algorithm specified",
        }

        actual_response = client.post(
            "/link/dibbs", json={"bundle": test_bundle, "algorithm": "INVALID"}
        )

        assert actual_response.json() == expected_response
        assert actual_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLink:
    @pytest.fixture
    def patients(self):
        bundle = load_test_json_asset("simple_patient_bundle_to_link_with_mpi.json")
        patients: list[schemas.PIIRecord] = []
        for entry in bundle["entry"]:
            if entry.get("resource", {}).get("resourceType", {}) == "Patient":
                patients.append(fhir.fhir_record_to_pii_record(entry["resource"]))
        return patients

    @mock.patch("recordlinker.database.algorithm_service.default_algorithm")
    def test_link_success(self, patched_subprocess, basic_algorithm, patients, client):
        patched_subprocess.return_value = basic_algorithm
        response_1 = client.post(
            "/link", json={"record": json.loads(patients[0].model_dump_json(exclude_none=True))}
        )
        person_1 = response_1.json()["person_reference_id"]
        assert response_1.json()["prediction"] == "no_match"

        response_2 = client.post(
            "/link", json={"record": json.loads(patients[1].model_dump_json(exclude_none=True))}
        )
        person_2 = response_2.json()["person_reference_id"]
        assert response_2.json()["prediction"] == "match"
        assert person_2 == person_1

        response_3 = client.post(
            "/link", json={"record": json.loads(patients[2].model_dump_json(exclude_none=True))}
        )
        assert response_3.json()["prediction"] == "no_match"

        # Cluster membership success--justified match
        response_4 = client.post(
            "/link", json={"record": json.loads(patients[3].model_dump_json(exclude_none=True))}
        )
        person_4 = response_4.json()["person_reference_id"]
        assert response_4.json()["prediction"] == "match"
        assert person_4 == person_1

        response_5 = client.post(
            "/link", json={"record": json.loads(patients[4].model_dump_json(exclude_none=True))}
        )
        assert response_5.json()["prediction"] == "no_match"

        response_6 = client.post(
            "/link", json={"record": json.loads(patients[5].model_dump_json(exclude_none=True))}
        )
        assert response_6.json()["prediction"] == "no_match"

    @mock.patch("recordlinker.database.algorithm_service.get_algorithm")
    def test_link_enhanced_algorithm(
        self, patched_subprocess, enhanced_algorithm, patients, client
    ):
        patched_subprocess.return_value = enhanced_algorithm

        response_1 = client.post(
            "/link",
            json={
                "record": json.loads(patients[0].model_dump_json(exclude_none=True)),
                "algorithm": "dibbs-enhanced",
            },
        )
        person_1 = response_1.json()["person_reference_id"]
        assert response_1.json()["prediction"] == "no_match"

        response_2 = client.post(
            "/link",
            json={
                "record": json.loads(patients[1].model_dump_json(exclude_none=True)),
                "algorithm": "dibbs-enhanced",
            },
        )
        person_2 = response_2.json()["person_reference_id"]
        assert response_2.json()["prediction"] == "match"
        assert person_2 == person_1

        response_3 = client.post(
            "/link",
            json={
                "record": json.loads(patients[2].model_dump_json(exclude_none=True)),
                "algorithm": "dibbs-enhanced",
            },
        )
        assert response_3.json()["prediction"] == "no_match"

        # Cluster membership success--justified match
        response_4 = client.post(
            "/link",
            json={
                "record": json.loads(patients[3].model_dump_json(exclude_none=True)),
                "algorithm": "dibbs-enhanced",
            },
        )
        person_4 = response_4.json()["person_reference_id"]
        assert response_4.json()["prediction"] == "match"
        assert person_4 == person_1

        response_5 = client.post(
            "/link",
            json={
                "record": json.loads(patients[4].model_dump_json(exclude_none=True)),
                "algorithm": "dibbs-enhanced",
            },
        )
        assert response_5.json()["prediction"] == "no_match"

        response_6 = client.post(
            "/link",
            json={
                "record": json.loads(patients[5].model_dump_json(exclude_none=True)),
                "algorithm": "dibbs-enhanced",
            },
        )
        assert response_6.json()["prediction"] == "no_match"

    @mock.patch("recordlinker.database.algorithm_service.get_algorithm")
    def test_link_invalid_algorithm_param(self, patched_subprocess, patients, client):
        patched_subprocess.return_value = None
        actual_response = client.post(
            "/link",
            json={
                "record": json.loads(patients[0].model_dump_json(exclude_none=True)),
                "algorithm": "INVALID",
            },
        )

        assert actual_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert actual_response.json()["detail"] == "Error: No algorithm found"

    @mock.patch("recordlinker.database.algorithm_service.default_algorithm")
    def test_link_no_default_algorithm(self, patched_subprocess, patients, client):
        patched_subprocess.return_value = None
        actual_response = client.post(
            "/link",
            json={
                "record": json.loads(patients[0].model_dump_json(exclude_none=True)),
                "algorithm": "INVALID",
            },
        )

        assert actual_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert actual_response.json()["detail"] == "Error: No algorithm found"

class TestLinkFHIR:
    @mock.patch("recordlinker.database.algorithm_service.default_algorithm")
    def test_linkrecord_bundle_with_no_patient(self, patched_subprocess, basic_algorithm, client):
        patched_subprocess.return_value = basic_algorithm
        bad_bundle = {"entry": []}
        actual_response = client.post(
            "/link/fhir",
            json={"bundle": bad_bundle},
        )

        assert actual_response.status_code == status.HTTP_400_BAD_REQUEST
        assert actual_response.json()["detail"] == "Error: Supplied bundle contains no Patient resource to link on."

    @mock.patch("recordlinker.database.algorithm_service.default_algorithm")
    def test_link_success(self, patched_subprocess, basic_algorithm, client):
        patched_subprocess.return_value = basic_algorithm
        test_bundle = load_test_json_asset("patient_bundle_to_link_with_mpi.json")
        entry_list = copy.deepcopy(test_bundle["entry"])
        print(basic_algorithm)

        bundle_1 = test_bundle
        bundle_1["entry"] = [entry_list[0]]
        response_1 = client.post("/link/fhir", json={"bundle": bundle_1})
        person_1 = response_1.json()["person_reference_id"]
        assert response_1.json()["prediction"] == "no_match"

        bundle_2 = test_bundle
        bundle_2["entry"] = [entry_list[1]]
        response_2 = client.post("/link/fhir", json={"bundle": bundle_2})
        person_2 = response_2.json()["person_reference_id"]
        assert response_2.json()["prediction"] == "match" # Blocks on Pass 1, fuzzy match first name yes, exact match last name yes; fails of Pass 2
        assert person_2 == person_1

        bundle_3 = test_bundle
        bundle_3["entry"] = [entry_list[2]]
        response_3 = client.post("/link/fhir", json={"bundle": bundle_3})
        assert response_3.json()["prediction"] == "no_match"

        # Cluster membership success--justified match
        bundle_4 = test_bundle
        bundle_4["entry"] = [entry_list[3]]
        response_4 = client.post("/link/fhir", json={"bundle": bundle_4})
        person_4 = response_4.json()["person_reference_id"]
        assert response_4.json()["prediction"] == "match"
        assert person_4 == person_1

        bundle_5 = test_bundle
        bundle_5["entry"] = [entry_list[4]]
        response_5 = client.post("/link/fhir", json={"bundle": bundle_5})
        assert response_5.json()["prediction"] == "no_match"

        bundle_6 = test_bundle
        bundle_6["entry"] = [entry_list[5]]
        response_6 = client.post("/link/fhir", json={"bundle": bundle_6})
        assert response_6.json()["prediction"] == "no_match"
    
    @mock.patch("recordlinker.database.algorithm_service.get_algorithm")
    def test_link_enhanced_algorithm(
        self, patched_subprocess, enhanced_algorithm, client
    ):
        patched_subprocess.return_value = enhanced_algorithm
        test_bundle = load_test_json_asset("patient_bundle_to_link_with_mpi.json")
        entry_list = copy.deepcopy(test_bundle["entry"])

        bundle_1 = test_bundle
        bundle_1["entry"] = [entry_list[0]]
        response_1 = client.post(
            "/link/fhir", json={"bundle": bundle_1, "algorithm": "dibbs-enhanced"}
        )
        person_1 = response_1.json()["person_reference_id"]
        assert response_1.json()["prediction"] == "no_match"

        bundle_2 = test_bundle
        bundle_2["entry"] = [entry_list[1]]
        response_2 = client.post(
            "/link/fhir", json={"bundle": bundle_2, "algorithm": "dibbs-enhanced"}
        )
        person_2 = response_2.json()["person_reference_id"]
        assert response_2.json()["prediction"] == "match"
        assert person_2 == person_1

        bundle_3 = test_bundle
        bundle_3["entry"] = [entry_list[2]]
        response_3 = client.post(
            "/link/fhir", json={"bundle": bundle_3, "algorithm": "dibbs-enhanced"}
        )
        assert response_3.json()["prediction"] == "no_match"

        # Cluster membership success--justified match
        bundle_4 = test_bundle
        bundle_4["entry"] = [entry_list[3]]
        response_4 = client.post(
            "/link/fhir", json={"bundle": bundle_4, "algorithm": "dibbs-enhanced"}
        )
        person_4 = response_4.json()["person_reference_id"]
        assert response_4.json()["prediction"] == "match"
        assert person_4 == person_1

        bundle_5 = test_bundle
        bundle_5["entry"] = [entry_list[4]]
        response_5 = client.post(
            "/link/fhir", json={"bundle": bundle_5, "algorithm": "dibbs-enhanced"}
        )
        assert response_5.json()["prediction"] == "no_match"

        bundle_6 = test_bundle
        bundle_6["entry"] = [entry_list[5]]
        response_6 = client.post(
            "/link/fhir", json={"bundle": bundle_6, "algorithm": "dibbs-enhanced"}
        )
        assert response_6.json()["prediction"] == "no_match"
    
    @mock.patch("recordlinker.database.algorithm_service.get_algorithm")
    def test_linkrecord_invalid_algorithm_param(self, patched_subprocess, client):
        patched_subprocess.return_value = None
        test_bundle = load_test_json_asset("patient_bundle_to_link_with_mpi.json")

        actual_response = client.post(
            "/link/fhir", json={"bundle": test_bundle, "algorithm": "INVALID"}
        )

        assert actual_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert actual_response.json()["detail"] == "Error: No algorithm found"

    @mock.patch("recordlinker.database.algorithm_service.default_algorithm")
    def test_linkrecord_no_default_algorithm(self, patched_subprocess, client):
        patched_subprocess.return_value = None
        test_bundle = load_test_json_asset("patient_bundle_to_link_with_mpi.json")

        actual_response = client.post(
            "/link/fhir", json={"bundle": test_bundle, "algorithm": "INVALID"}
        )

        assert actual_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert actual_response.json()["detail"] == "Error: No algorithm found"

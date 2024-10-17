import copy
import json
import pytest
from unittest import mock

from fastapi import status

from recordlinker import utils
from recordlinker import schemas
from recordlinker.linking import link

def test_health_check(client):
    actual_response = client.get("/")
    assert actual_response.status_code == 200
    assert actual_response.json() == {"status": "OK"}

def test_openapi(client):
    actual_response = client.get("/openapi.json")
    assert actual_response.status_code == 200


class TestLinkRecord:
    @mock.patch("recordlinker.linking.algorithm_service.default_algorithm")
    def test_linkrecord_bundle_with_no_patient(self, patched_subprocess, basic_algorithm, client):
        patched_subprocess.return_value = basic_algorithm
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

    @mock.patch("recordlinker.linking.algorithm_service.default_algorithm")
    def test_linkrecord_success(self, patched_subprocess, basic_algorithm, client):
        patched_subprocess.return_value = basic_algorithm
        test_bundle = utils.read_json_from_assets("patient_bundle_to_link_with_mpi.json")
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
        assert not resp_6.json()["found_match"]

    @mock.patch("recordlinker.linking.algorithm_service.get_algorithm")
    def test_linkrecord_enhanced_algo(self, patched_subprocess, enhanced_algorithm, client):
        patched_subprocess.return_value = enhanced_algorithm
        test_bundle = utils.read_json_from_assets("patient_bundle_to_link_with_mpi.json")
        entry_list = copy.deepcopy(test_bundle["entry"])

        bundle_1 = test_bundle
        bundle_1["entry"] = [entry_list[0]]
        resp_1 = client.post("/link-record", json={"bundle": bundle_1, "algorithm": "dibbs-enhanced"})
        new_bundle = resp_1.json()["updated_bundle"]
        person_1 = [
            r.get("resource")
            for r in new_bundle["entry"]
            if r.get("resource").get("resourceType") == "Person"
        ][0]
        assert not resp_1.json()["found_match"]

        bundle_2 = test_bundle
        bundle_2["entry"] = [entry_list[1]]
        resp_2 = client.post("/link-record", json={"bundle": bundle_2, "algorithm": "dibbs-enhanced"})
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
        resp_3 = client.post("/link-record", json={"bundle": bundle_3, "algorithm": "dibbs-enhanced"})
        assert not resp_3.json()["found_match"]

        bundle_4 = test_bundle
        bundle_4["entry"] = [entry_list[3]]
        resp_4 = client.post("/link-record", json={"bundle": bundle_4, "algorithm": "dibbs-enhanced"})
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
        resp_5 = client.post("/link-record", json={"bundle": bundle_5, "algorithm": "dibbs-enhanced"})
        assert not resp_5.json()["found_match"]

        bundle_6 = test_bundle
        bundle_6["entry"] = [entry_list[5]]
        resp_6 = client.post("/link-record", json={"bundle": bundle_6, "algorithm": "dibbs-enhanced"})
        new_bundle = resp_6.json()["updated_bundle"]
        assert not resp_6.json()["found_match"]


    @mock.patch("recordlinker.linking.algorithm_service.get_algorithm")
    def test_linkrecord_invalid_algorithm_param(self, patched_subprocess, client):
        patched_subprocess.return_value = None
        test_bundle = utils.read_json_from_assets("patient_bundle_to_link_with_mpi.json")
        expected_response = {
            "found_match": False,
            "updated_bundle": test_bundle,
            "message": "Error: Invalid algorithm specified",
        }

        actual_response = client.post(
            "/link-record", json={"bundle": test_bundle, "algorithm": "INVALID"}
        )

        assert actual_response.json() == expected_response
        assert actual_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

class TestLink:
    @pytest.fixture
    def patients(self):
        bundle = utils.read_json_from_assets("linking", "patient_bundle_to_link_with_mpi.json")
        patients: list[schemas.PIIRecord] = []
        for entry in bundle["entry"]:
            if entry.get("resource", {}).get("resourceType", {}) == "Patient":
                patients.append(link.fhir_record_to_pii_record(entry["resource"]))
        return patients

    @mock.patch("recordlinker.linking.algorithm_service.default_algorithm")
    def test_link_success(self, patched_subprocess, basic_algorithm, patients, client):
        patched_subprocess.return_value = basic_algorithm

        response_1 = client.post("/link", json={"record": json.loads(patients[0].model_dump_json(exclude_none=True))})
        person_1 = response_1.json()["person_reference_id"]
        assert not response_1.json()["is_match"]

        response_2 = client.post("/link", json={"record": json.loads(patients[1].model_dump_json(exclude_none=True))})
        person_2 = response_2.json()["person_reference_id"]
        assert response_2.json()["is_match"]
        assert person_2 == person_1
    
        response_3 = client.post("/link", json={"record": json.loads(patients[2].model_dump_json(exclude_none=True))})
        assert not response_3.json()["is_match"]

        # Cluster membership success--justified match
        response_4 = client.post("/link", json={"record": json.loads(patients[3].model_dump_json(exclude_none=True))})
        person_4 = response_4.json()["person_reference_id"]
        assert response_4.json()["is_match"]
        assert person_4 == person_1

        response_5 = client.post("/link", json={"record": json.loads(patients[4].model_dump_json(exclude_none=True))})
        assert not response_5.json()["is_match"]

        response_6 = client.post("/link", json={"record": json.loads(patients[5].model_dump_json(exclude_none=True))})
        assert not response_6.json()["is_match"]

    @mock.patch("recordlinker.linking.algorithm_service.get_algorithm")
    def test_link_enhanced_algorithm(self, patched_subprocess, enhanced_algorithm, patients, client):
        patched_subprocess.return_value = enhanced_algorithm

        response_1 = client.post("/link", json={"record": json.loads(patients[0].model_dump_json(exclude_none=True)), "algorithm": "dibbs-enhanced"})
        person_1 = response_1.json()["person_reference_id"]
        assert not response_1.json()["is_match"]

        response_2 = client.post("/link", json={"record": json.loads(patients[1].model_dump_json(exclude_none=True)), "algorithm": "dibbs-enhanced"})
        person_2 = response_2.json()["person_reference_id"]
        assert response_2.json()["is_match"]
        assert person_2 == person_1
    
        response_3 = client.post("/link", json={"record": json.loads(patients[2].model_dump_json(exclude_none=True)), "algorithm": "dibbs-enhanced"})
        assert not response_3.json()["is_match"]

        # Cluster membership success--justified match
        response_4 = client.post("/link", json={"record": json.loads(patients[3].model_dump_json(exclude_none=True)), "algorithm": "dibbs-enhanced"})
        person_4 = response_4.json()["person_reference_id"]
        assert response_4.json()["is_match"]
        assert person_4 == person_1

        response_5 = client.post("/link", json={"record": json.loads(patients[4].model_dump_json(exclude_none=True)), "algorithm": "dibbs-enhanced"})
        assert not response_5.json()["is_match"]

        response_6 = client.post("/link", json={"record": json.loads(patients[5].model_dump_json(exclude_none=True)), "algorithm": "dibbs-enhanced"})
        assert not response_6.json()["is_match"]

    @mock.patch("recordlinker.linking.algorithm_service.get_algorithm")
    def test_link_invalid_algorithm_param(self, patched_subprocess, patients, client):
        patched_subprocess.return_value = None
        actual_response = client.post(
            "/link", json={"record": json.loads(patients[0].model_dump_json(exclude_none=True)), "algorithm": "INVALID"}
        )

        assert actual_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert actual_response.json()["detail"] == "Error: Invalid algorithm specified"

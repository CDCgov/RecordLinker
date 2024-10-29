"""
unit.linking.test_link.py
~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.linking.link module.
"""

import collections
import copy
import uuid

import pytest
from conftest import load_json_asset

from recordlinker import models
from recordlinker import schemas
from recordlinker.linking import link


class TestAddPersonResource:
    def test_add_person_resource(self):
        bundle = load_json_asset("patient_bundle.json")
        raw_bundle = copy.deepcopy(bundle)
        patient_id = "TEST_PATIENT_ID"
        person_id = "TEST_PERSON_ID"

        returned_bundle = link.add_person_resource(
            person_id=person_id, patient_id=patient_id, bundle=raw_bundle
        )

        # Assert returned_bundle has added element in "entry"
        assert len(returned_bundle.get("entry")) == len(bundle.get("entry")) + 1

        # Assert the added element is the person_resource bundle
        assert returned_bundle.get("entry")[-1].get("resource").get("resourceType") == "Person"
        assert returned_bundle.get("entry")[-1].get("request").get("url") == "Person/TEST_PERSON_ID"


class TestCompare:
    def test_compare_match(self):
        rec = schemas.PIIRecord(
            **{
                "name": [
                    {
                        "given": [
                            "John",
                        ],
                        "family": "Doe",
                    }
                ]
            }
        )
        pat = models.Patient(
            data={
                "name": [
                    {
                        "given": [
                            "John",
                        ],
                        "family": "Doey",
                    }
                ]
            }
        )

        algorithm_pass = models.AlgorithmPass(
            id=1,
            algorithm_id=1,
            blocking_keys=[1],
            evaluators={
                "FIRST_NAME": "func:recordlinker.linking.matchers.feature_match_exact",
                "LAST_NAME": "func:recordlinker.linking.matchers.feature_match_fuzzy_string",
            },
            rule="func:recordlinker.linking.matchers.eval_perfect_match",
            cluster_ratio=1.0,
            kwargs={},
        )

        assert link.compare(rec, pat, algorithm_pass) is True

    def test_compare_no_match(self):
        rec = schemas.PIIRecord(
            **{
                "name": [
                    {
                        "given": [
                            "John",
                        ],
                        "family": "Doe",
                    }
                ]
            }
        )
        pat = models.Patient(
            data={
                "name": [
                    {
                        "given": [
                            "John",
                        ],
                        "family": "Doey",
                    }
                ]
            }
        )
        algorithm_pass = models.AlgorithmPass(
            id=1,
            algorithm_id=1,
            blocking_keys=[1],
            evaluators={
                "FIRST_NAME": "func:recordlinker.linking.matchers.feature_match_exact",
                "LAST_NAME": "func:recordlinker.linking.matchers.feature_match_exact",
            },
            rule="func:recordlinker.linking.matchers.eval_perfect_match",
            cluster_ratio=1.0,
            kwargs={},
        )

        assert link.compare(rec, pat, algorithm_pass) is False


class TestLinkRecordAgainstMpi:
    # TODO: Add test case for last name O'Neil
    @pytest.fixture
    def patients(self):
        bundle = load_json_asset("simple_patient_bundle_to_link_with_mpi.json")
        patients = []
        patients: list[schemas.PIIRecord] = []
        for entry in bundle["entry"]:
            if entry.get("resource", {}).get("resourceType", {}) == "Patient":
                patients.append(link.fhir_record_to_pii_record(entry["resource"]))
        return patients

    def test_basic_match_one(self, session, basic_algorithm, patients):
        # Test various null data values in incoming record
        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        for patient in patients[:2]:
            matched, pid, _ = link.link_record_against_mpi(patient, session, basic_algorithm)
            matches.append(matched)
            mapped_patients[pid] += 1

        # First patient inserted into empty MPI, no match
        # Second patient blocks with first patient in first pass, then fuzzy matches name
        assert matches == [False, True]
        assert sorted(list(mapped_patients.values())) == [2]

    def test_basic_match_two(self, session, basic_algorithm, patients):
        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        for patient in patients:
            matched, pid, _ = link.link_record_against_mpi(patient, session, basic_algorithm)
            matches.append(matched)
            mapped_patients[pid] += 1

        # First patient inserted into empty MPI, no match
        # Second patient blocks with first patient in first pass, then fuzzy matches name
        # Third patient is entirely new individual, no match
        # Fourth patient fails blocking in first pass, blocks with first patient in second
        # pass, then fuzzy matches on address and exact matches on birthdate, joins cluster
        # with first and second patient
        # Fifth patient: fails blocking in first and second pass, no match
        # Sixth patient: fails blocking in first pass, blocks with fifth patient in second pass,
        # then matches on birthdate but fails on address, no match
        assert matches == [False, True, False, True, False, False]
        assert sorted(list(mapped_patients.values())) == [1, 1, 1, 3]

    def test_enhanced_match_three(self, session, enhanced_algorithm, patients: list[schemas.PIIRecord]):
        # add an additional patient that will fuzzy match to patient 0
        patient0_copy = copy.deepcopy(patients[0])
        patient0_copy.external_id = str(uuid.uuid4())
        patient0_copy.name[0].given[0] = "Jhon"
        patients.append(patient0_copy)
        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        for patient in patients:
            matched, pid, _ = link.link_record_against_mpi(patient, session, enhanced_algorithm)
            matches.append(matched)
            mapped_patients[pid] += 1

        # First patient inserted into empty MPI, no match
        # Second patient blocks with first patient in first pass, then fuzzy matches name
        # Third patient is entirely new individual, no match
        # Fourth patient fails blocking with first pass but catches on second, fuzzy matches
        # Fifth patient: in first pass MRN blocks with one cluster but fails name,
        #  in second pass name blocks with different cluster but fails address, no match
        # Sixth patient: in first pass, MRN blocks with one cluster and name matches in it,
        # in second pass name blocks on different cluster and address matches it,
        #  finds greatest strength match and correctly assigns to larger cluster
        assert matches == [False, True, False, True, False, False, True]
        assert sorted(list(mapped_patients.values())) == [1, 1, 1, 4]

def test_fhir_record_to_pii_record():
    fhir_record = {
        "resourceType": "Patient",
        "id": "f6a16ff7-4a31-11eb-be7b-8344edc8f36b",
        "identifier": [
            {
                "value": "1234567890",
                "type": {
                    "coding": [{
                        "code": "MR",
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                        "display": "Medical record number"
                    }]
                },
            },
            {
                "system" : "http://hl7.org/fhir/sid/us-ssn",
                "value" : "111223333",
                "type" : {
                    "coding" : [{
                        "system" : "http://terminology.hl7.org/CodeSystem/v2-0203",
                        "code" : "SS"
                    }]
                },
            }
        ],
        "name": [
            {
                "family": "Shepard",
                "given": [
                "John"
                ],
                "use": "official"
            }
        ],
        "birthDate": "2053-11-07",
        "gender": "male",
        "address": [
        {
            "line": [
            "1234 Silversun Strip"
            ],
            "buildingNumber": "1234",
            "city": "Boston",
            "state": "Massachusetts",
            "postalCode": "99999",
            "district": "county",
            "use": "home"
        }
        ],
        "telecom": [
            {
                "use": "home",
                "system": "phone",
                "value": "123-456-7890"
            }
        ],
        "extension" : [
            {
                "url" : "http://hl7.org/fhir/StructureDefinition/individual-genderIdentity",
                "extension" : [{
                    "url" : "value",
                    "valueCodeableConcept" : {
                        "coding" : [{
                            "system" : "http://snomed.info/sct",
                            "code" : "446141000124107",
                            "display" : "Identifies as female gender (finding)"
                        }]
                    }
                }]
            },
            {
                "url" : "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
                "extension": [
                    {
                        "url" : "ombCategory",
                        "valueCoding" : {
                            "system" : "urn:oid:2.16.840.1.113883.6.238",
                            "code" : "2106-3",
                            "display" : "White"
                        }
                    }
                ]
            }
        ]
    }

    pii_record = link.fhir_record_to_pii_record(fhir_record)

    assert pii_record.external_id == "f6a16ff7-4a31-11eb-be7b-8344edc8f36b"
    assert pii_record.name[0].family == "Shepard"
    assert pii_record.name[0].given == ["John"]
    assert str(pii_record.birth_date) == "2053-11-07"
    assert str(pii_record.sex) == "M"
    assert pii_record.address[0].line == ["1234 Silversun Strip"]
    assert pii_record.address[0].city == "Boston"
    assert pii_record.address[0].state == "Massachusetts"
    assert pii_record.address[0].postal_code == "99999"
    assert pii_record.address[0].county == "county"
    assert pii_record.mrn == "1234567890"
    assert pii_record.ssn == "111-22-3333"
    assert pii_record.telecom[0].value == "123-456-7890"
    assert pii_record.telecom[0].system == "phone"
    assert str(pii_record.race) == "WHITE"
    assert str(pii_record.gender) == "FEMALE"

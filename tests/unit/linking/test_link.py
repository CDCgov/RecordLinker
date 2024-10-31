"""
unit.linking.test_link.py
~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.linking.link module.
"""

import collections
import copy
import uuid

import pytest
from conftest import load_test_json_asset

from recordlinker import models
from recordlinker import schemas
from recordlinker.hl7 import fhir
from recordlinker.linking import link


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
            belongingness_ratio=[0.75, 1.0],
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
            belongingness_ratio=[0.75, 1.0],
            kwargs={},
        )

        assert link.compare(rec, pat, algorithm_pass) is False


class TestLinkRecordAgainstMpi:
    # TODO: Add test case for last name O'Neil
    @pytest.fixture
    def patients(self):
        bundle = load_test_json_asset("simple_patient_bundle_to_link_with_mpi.json")
        patients = []
        patients: list[schemas.PIIRecord] = []
        for entry in bundle["entry"]:
            if entry.get("resource", {}).get("resourceType", {}) == "Patient":
                patients.append(fhir.fhir_record_to_pii_record(entry["resource"]))
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

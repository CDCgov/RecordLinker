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
            evaluators=[
                {"feature": "FIRST_NAME", "func": "func:recordlinker.linking.matchers.compare_match_all"},
                {"feature": "LAST_NAME", "func": "func:recordlinker.linking.matchers.compare_fuzzy_match"},
            ],
            rule="func:recordlinker.linking.matchers.rule_match",
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
            evaluators=[
                {"feature": "FIRST_NAME", "func": "func:recordlinker.linking.matchers.compare_match_all"},
                {"feature": "LAST_NAME", "func": "func:recordlinker.linking.matchers.compare_match_all"},
            ],
            rule="func:recordlinker.linking.matchers.rule_match",
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

    @pytest.fixture
    def possible_match_basic_patients(self):
        bundle = load_test_json_asset("possible_match_basic_patient_bundle.json")
        patients = []
        patients: list[schemas.PIIRecord] = []
        for entry in bundle["entry"]:
            if entry.get("resource", {}).get("resourceType", {}) == "Patient":
                patients.append(fhir.fhir_record_to_pii_record(entry["resource"]))
        return patients
    
    @pytest.fixture
    def possible_match_enhanced_patients(self):
        bundle = load_test_json_asset("possible_match_enhanced_patient_bundle.json")
        patients = []
        patients: list[schemas.PIIRecord] = []
        for entry in bundle["entry"]:
            if entry.get("resource", {}).get("resourceType", {}) == "Patient":
                patients.append(fhir.fhir_record_to_pii_record(entry["resource"]))
        return patients
    
    @pytest.fixture
    def multiple_matches_patients(self):
        bundle = load_test_json_asset("multiple_matches_patient_bundle.json")
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
        for data in patients[:2]:
            (patient, person, results) = link.link_record_against_mpi(data, session, basic_algorithm)
            matches.append(bool(person and results))
            mapped_patients[person.reference_id] += 1

        # First patient inserted into empty MPI, no match
        # Second patient blocks with first patient in first pass, then fuzzy matches name
        assert matches == [False, True]
        assert sorted(list(mapped_patients.values())) == [2]

    def test_basic_match_two(self, session, basic_algorithm, patients):
        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        for data in patients:
            (patient, person, results) = link.link_record_against_mpi(data, session, basic_algorithm)
            matches.append(bool(person and results))
            mapped_patients[person.reference_id] += 1

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


    def test_basic_possible_match(
        self,
        session,
        basic_algorithm,
        possible_match_basic_patients: list[schemas.PIIRecord]
        ):
        predictions: dict[str, dict] = collections.defaultdict(dict)
        # Decrease Belongingness Ratio lower bound to catch Possible Match when Belongingness Ratio = 0.5
        for lower_bound in [0.5, 0.45]: # test >= lower bound
            basic_algorithm.belongingness_ratio_lower_bound = lower_bound
            for i, data in enumerate(possible_match_basic_patients):
                (patient, person, results) = link.link_record_against_mpi(data, session, basic_algorithm)
                predictions[i] = {
                    "patient": patient,
                    "person": person,
                    "results": results
                }
            # 1 Possible Match
            assert not predictions[2]["person"]
            assert len(predictions[2]["results"]) == 1
            assert predictions[2]["results"][0].person == predictions[0]["person"]
            assert predictions[2]["results"][0].belongingness_ratio >= basic_algorithm.belongingness_ratio_lower_bound
            assert predictions[2]["results"][0].belongingness_ratio < basic_algorithm.belongingness_ratio_upper_bound


    def test_enhanced_match_three(self, session, enhanced_algorithm, patients: list[schemas.PIIRecord]):
        # add an additional patient that will fuzzy match to patient 0
        patient0_copy = copy.deepcopy(patients[0])
        patient0_copy.external_id = str(uuid.uuid4())
        patient0_copy.name[0].given[0] = "Jhon"
        patients.append(patient0_copy)
        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        for data in patients:
            (patient, person, results) = link.link_record_against_mpi(data, session, enhanced_algorithm)
            matches.append(bool(person and results))
            mapped_patients[person.reference_id] += 1

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


    def test_enhanced_possible_match(
            self,
            session,
            enhanced_algorithm,
            possible_match_enhanced_patients: list[schemas.PIIRecord]
        ):
        predictions: dict[str, dict] = collections.defaultdict(dict)
        # Decrease Belongingness Ratio lower bound to catch Possible Match when Belongingness Ratio = 0.5
        for lower_bound in [0.5, 0.45]: # test >= lower bound
            enhanced_algorithm.belongingness_ratio_lower_bound = lower_bound
            for i, data in enumerate(possible_match_enhanced_patients):
                (patient, person, results) = link.link_record_against_mpi(data, session, enhanced_algorithm)
                predictions[i] = {
                    "patient": patient,
                    "person": person,
                    "results": results
                }
            # 1 Possible Match
            assert not predictions[2]["person"]
            assert len(predictions[2]["results"]) == 1
            assert predictions[2]["results"][0].person == predictions[0]["person"]
            assert predictions[2]["results"][0].belongingness_ratio >= enhanced_algorithm.belongingness_ratio_lower_bound
            assert predictions[2]["results"][0].belongingness_ratio < enhanced_algorithm.belongingness_ratio_upper_bound


    def test_include_multiple_matches_true(
            self,
            session,
            basic_algorithm,
            multiple_matches_patients: list[schemas.PIIRecord]
        ):
        predictions: dict[str, dict] = collections.defaultdict(dict)
        # Adjust Belongingness Ratio bounds to catch Match when Belongingness Ratio = 0.5
        basic_algorithm.belongingness_ratio_lower_bound = 0.3
        for upper_bound in [0.5, 0.45]: # test >= upper bound
            basic_algorithm.belongingness_ratio_upper_bound = upper_bound
            for i, data in enumerate(multiple_matches_patients):
                (patient, person, results) = link.link_record_against_mpi(data, session, basic_algorithm)
                predictions[i] = {
                    "patient": patient,
                    "person": person,
                    "results": results
                }
            # 2 Matches
            assert len(predictions[3]["results"]) == 2
            assert predictions[3]["person"] == predictions[1]["person"] # Assign to Person with highest Belongingness Ratio (1.0)
            for match in predictions[2]["results"]:
                assert match.belongingness_ratio >= basic_algorithm.belongingness_ratio_upper_bound


    def test_include_multiple_matches_false(
            self,
            session,
            basic_algorithm,
            multiple_matches_patients: list[schemas.PIIRecord]
        ):
        predictions: dict[str, dict] = collections.defaultdict(dict)
        basic_algorithm.include_multiple_matches = False
        # Adjust Belongingness Ratio bounds to catch Match when Belongingness Ratio = 0.5
        basic_algorithm.belongingness_ratio_lower_bound = 0.3
        for upper_bound in [0.5, 0.45]: # test >= upper bound
            basic_algorithm.belongingness_ratio_upper_bound = upper_bound
            for i, data in enumerate(multiple_matches_patients):
                (patient, person, results) = link.link_record_against_mpi(data, session, basic_algorithm)
                predictions[i] = {
                    "patient": patient,
                    "person": person,
                    "results": results
                }
            # 2 Matches, but only include 1
            assert len(predictions[3]["results"]) == 1
            assert predictions[3]["person"] == predictions[1]["person"] # Assign to Person with highest Belongingness Ratio (1.0)
            assert predictions[3]["results"][0].belongingness_ratio >= basic_algorithm.belongingness_ratio_upper_bound

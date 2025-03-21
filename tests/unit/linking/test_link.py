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

        evaluators = [
            {"feature": "FIRST_NAME", "func": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match"},
            {"feature": "LAST_NAME", "func": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match"},
        ]
        log_odds = {"FIRST_NAME": 6.85, "LAST_NAME": 6.35}
        eval_fields = [e["feature"] for e in evaluators]
        max_points = sum([log_odds[e] for e in eval_fields])
        max_allowed_missingness_proportion = 0.5
        missing_field_points_proportion = 0.5

        algorithm_pass = models.AlgorithmPass(
            id=1,
            algorithm_id=1,
            blocking_keys=[1],
            evaluators=evaluators,
            rule="func:recordlinker.linking.matchers.rule_probabilistic_match",
            kwargs={"log_odds": log_odds, "true_match_threshold": 12},
        )

        assert link.compare(rec, pat, max_points, max_allowed_missingness_proportion, missing_field_points_proportion, algorithm_pass) is True

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
        evaluators = [
            {"feature": "FIRST_NAME", "func": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match"},
            {"feature": "LAST_NAME", "func": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match"},
        ]
        log_odds = {"FIRST_NAME": 6.85, "LAST_NAME": 6.35}
        eval_fields = [e["feature"] for e in evaluators]
        max_points = sum([log_odds[e] for e in eval_fields])
        max_allowed_missingness_proportion = 0.5
        missing_field_points_proportion = 0.5
        algorithm_pass = models.AlgorithmPass(
            id=1,
            algorithm_id=1,
            blocking_keys=[1],
            evaluators=evaluators,
            rule="func:recordlinker.linking.matchers.rule_probabilistic_match",
            kwargs={"log_odds": log_odds, "true_match_threshold": 12.95},
        )

        assert link.compare(rec, pat, max_points, max_allowed_missingness_proportion, missing_field_points_proportion, algorithm_pass) is False

    def test_compare_identifier_match(self):
        rec = schemas.PIIRecord(
            **{
                "identifiers": [
                    {
                        "type": "MR",
                        "authority": "CA",
                        "value": "123456789"
                    },
                    {
                        "type": "SS",
                        "authority": "VA",
                        "value": "987-65-4321"
                    }
                ]
            }
        )
        pat = models.Patient(
            data={
                "identifiers": [
                    {
                        "type": "MR",
                        "authority": "CA",
                        "value": "123456789"
                    },
                    {
                        "type": "SS",
                        "authority": "VA",
                        "value": "987-65-4321"
                    }
                ]
            }
        )

        evaluators = [
            {"feature": "IDENTIFIER", "func": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match"}
        ]
        log_odds = {"IDENTIFIER": 0.35}
        eval_fields = [e["feature"] for e in evaluators]
        max_points = sum([log_odds[e] for e in eval_fields])
        max_allowed_missingness_proportion = 0.5
        missing_field_points_proportion = 0.5

        algorithm_pass = models.AlgorithmPass(
            id=1,
            algorithm_id=1,
            blocking_keys=[1],
            evaluators=evaluators,
            rule="func:recordlinker.linking.matchers.rule_probabilistic_match",
            kwargs={"log_odds": log_odds, "true_match_threshold": 0.3},
        )

        assert link.compare(rec, pat, max_points, max_allowed_missingness_proportion, missing_field_points_proportion, algorithm_pass) is True

    def test_compare_identifier_with_suffix(self):
        rec = schemas.PIIRecord(
            **{
                "identifiers": [
                    {
                        "type": "MR",
                        "authority": "CA",
                        "value": "123456789"
                    },
                    {
                        "type": "SS",
                        "authority": "VA",
                        "value": "111-11-1111"
                    }
                ]
            }
        )
        pat = models.Patient(
            data={
                "identifiers": [
                    {
                        "type": "MR",
                        "authority": "CA",
                        "value": "123456789"
                    },
                    {
                        "type": "SS",
                        "authority": "VA",
                        "value": "987-65-4321"
                    }
                ]
            }
        )

        evaluators = [
            {"feature": "IDENTIFIER", "func": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match"}
        ]
        log_odds = {"IDENTIFIER": 0.35}
        eval_fields = [e["feature"] for e in evaluators]
        max_points = sum([log_odds[e] for e in eval_fields])
        max_allowed_missingness_proportion = 0.5
        missing_field_points_proportion = 0.5

        algorithm_pass = models.AlgorithmPass(
            id=1,
            algorithm_id=1,
            blocking_keys=[1],
            evaluators=evaluators,
            rule="func:recordlinker.linking.matchers.rule_probabilistic_match",
            kwargs={"log_odds": log_odds, "true_match_threshold": 0.3},
        )

        #should pass as MR is the same for both
        assert link.compare(rec, pat, max_points, max_allowed_missingness_proportion, missing_field_points_proportion, algorithm_pass) is True

        algorithm_pass.evaluators = [{"feature": "IDENTIFIER:SS", "func": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match"}]
        #should fail as SS is different for both
        assert link.compare(rec, pat, max_points, max_allowed_missingness_proportion, missing_field_points_proportion, algorithm_pass) is False

    def test_compare_invalid_feature(self):
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
                {"feature": "FIRST_NAME:DL", "func": "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match"},
            ],
            rule="func:recordlinker.linking.matchers.rule_probabilistic_match",
            kwargs={},
        )

        with pytest.raises(ValueError):
            link.compare(rec, pat, 0.0, 0.5, 0.5, algorithm_pass)


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
    def possible_match_default_patients(self):
        bundle = load_test_json_asset("possible_match_default_patient_bundle.json")
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

    def test_default_match_one(self, session, default_algorithm, patients):
        # Test various null data values in incoming record
        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        for data in patients[:2]:
            (_, person, results, _) = link.link_record_against_mpi(data, session, default_algorithm)
            matches.append(bool(person and results))
            mapped_patients[person.reference_id] += 1

        # First patient inserted into empty MPI, no match
        # Second patient blocks with first patient in first pass, then fuzzy matches name
        assert matches == [False, True]
        assert sorted(list(mapped_patients.values())) == [2]

    def test_default_match_two(self, session, default_algorithm, patients):
        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        for data in patients:
            (_, person, results, _) = link.link_record_against_mpi(data, session, default_algorithm)
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

    def test_default_match_three(self, session, default_algorithm, patients: list[schemas.PIIRecord]):
        # add an additional patient that will fuzzy match to patient 0
        patient0_copy = copy.deepcopy(patients[0])
        patient0_copy.external_id = str(uuid.uuid4())
        patient0_copy.name[0].given[0] = "Jhon"
        patients.append(patient0_copy)
        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        for data in patients:
            (_, person, results, _) = link.link_record_against_mpi(data, session, default_algorithm)
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
    
    def test_match_with_missing_field(
            self,
            session,
            default_algorithm,
            patients: list[schemas.PIIRecord]
        ):
        # Make a deep copy of the first patient, then delete some info
        patients = [patients[0]]
        duplicate = copy.deepcopy(patients[0])
        duplicate.external_id = str(uuid.uuid4())
        duplicate.name[0].family = ""
        duplicate.address[0].line[0] = ""
        patients.append(duplicate)

        # Test whether we can successfully make a match if info is missing
        default_algorithm.passes[0].kwargs["true_match_threshold"] = 9.5
        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        for data in patients[:2]:
            (_, person, results, _) = link.link_record_against_mpi(data, session, default_algorithm)
            matches.append(bool(person and results))
            mapped_patients[person.reference_id] += 1

        # First patient inserted into empty MPI, no match
        # Second patient blocks in each pass, is missing a field, but is allowed to match
        assert matches == [False, True]
        assert sorted(list(mapped_patients.values())) == [2]

    def test_reject_too_many_missing_field(
            self,
            session,
            default_algorithm,
            patients: list[schemas.PIIRecord]
        ):
        # Make a deep copy of the first patient, then delete some info
        patients = [patients[0]]
        duplicate = copy.deepcopy(patients[0])
        duplicate.external_id = str(uuid.uuid4())
        duplicate.name[0].given[0] = ""
        duplicate.address[0].line[0] = ""
        patients.append(duplicate)

        # Test whether too many missing points causes failure
        default_algorithm.max_missing_allowed_proportion = 0.3
        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        for data in patients[:2]:
            (_, person, results, _) = link.link_record_against_mpi(data, session, default_algorithm)
            matches.append(bool(person and results))
            mapped_patients[person.reference_id] += 1

        # First patient inserted into empty MPI, no match
        # Second patient blocks in each pass but missing too much data, fails
        assert matches == [False, False]

    def test_default_possible_match(
            self,
            session,
            default_algorithm,
            possible_match_default_patients: list[schemas.PIIRecord]
        ):
        predictions: dict[str, dict] = collections.defaultdict(dict)
        # Decrease Belongingness Ratio lower bound to catch Possible Match when Belongingness Ratio = 0.5
        for lower_bound in [0.5, 0.45]: # test >= lower bound
            default_algorithm.belongingness_ratio_lower_bound = lower_bound
            for i, data in enumerate(possible_match_default_patients):
                (patient, person, results, prediction) = link.link_record_against_mpi(data, session, default_algorithm)
                predictions[i] = {
                    "patient": patient,
                    "person": person,
                    "results": results,
                    "prediction": prediction
                }
            # 1 Possible Match
            assert not predictions[2]["person"]
            assert len(predictions[2]["results"]) == 1
            assert predictions[2]["results"][0].person == predictions[0]["person"]
            assert predictions[2]["results"][0].belongingness_ratio >= default_algorithm.belongingness_ratio_lower_bound
            assert predictions[2]["results"][0].belongingness_ratio < default_algorithm.belongingness_ratio_upper_bound
            assert predictions[2]["prediction"] == "possible_match"

    def test_include_multiple_matches_true(
            self,
            session,
            default_algorithm,
            multiple_matches_patients: list[schemas.PIIRecord]
        ):
        predictions: dict[str, dict] = collections.defaultdict(dict)
        # Adjust Belongingness Ratio bounds to catch Match when Belongingness Ratio = 0.5
        default_algorithm.belongingness_ratio_lower_bound = 0.3
        for upper_bound in [0.5, 0.45]: # test >= upper bound
            default_algorithm.belongingness_ratio_upper_bound = upper_bound
            for i, data in enumerate(multiple_matches_patients):
                (patient, person, results, prediction) = link.link_record_against_mpi(data, session, default_algorithm)
                predictions[i] = {
                    "patient": patient,
                    "person": person,
                    "results": results,
                    "prediction": prediction
                }
            # 2 Matches
            assert len(predictions[3]["results"]) == 2
            assert predictions[3]["person"] == predictions[1]["person"] # Assign to Person with highest Belongingness Ratio (1.0)
            for match in predictions[2]["results"]:
                assert match.belongingness_ratio >= default_algorithm.belongingness_ratio_upper_bound
            assert predictions[3]["prediction"] == "match"

    def test_include_multiple_matches_false(
            self,
            session,
            default_algorithm,
            multiple_matches_patients: list[schemas.PIIRecord]
        ):
        predictions: dict[str, dict] = collections.defaultdict(dict)
        default_algorithm.include_multiple_matches = False
        # Adjust Belongingness Ratio bounds to catch Match when Belongingness Ratio = 0.5
        default_algorithm.belongingness_ratio_lower_bound = 0.3
        for upper_bound in [0.5, 0.45]: # test >= upper bound
            default_algorithm.belongingness_ratio_upper_bound = upper_bound
            for i, data in enumerate(multiple_matches_patients):
                (patient, person, results, prediction) = link.link_record_against_mpi(data, session, default_algorithm)
                predictions[i] = {
                    "patient": patient,
                    "person": person,
                    "results": results,
                    "prediction": prediction
                }
            # 2 Matches, but only include 1
            assert len(predictions[3]["results"]) == 1
            assert predictions[3]["person"] == predictions[1]["person"] # Assign to Person with highest Belongingness Ratio (1.0)
            assert predictions[3]["results"][0].belongingness_ratio >= default_algorithm.belongingness_ratio_upper_bound
            assert predictions[3]["prediction"] == "match"

    def test_no_persist(self, session, default_algorithm, patients):
        # First patient inserted into MPI, no match
        first = patients[0]
        (pat1, per1, results, prediction) = link.link_record_against_mpi(first, session, default_algorithm, persist=True)
        assert prediction == "no_match"
        assert pat1 is not None
        assert per1 is not None
        assert not results
        # Second patient not inserted into MPI, match first person
        second = patients[1]
        (pat2, per2, results, prediction) = link.link_record_against_mpi(second, session, default_algorithm, persist=False)
        assert prediction == "match"
        assert pat2 is None
        assert per2 is not None
        assert per2.reference_id == per1.reference_id
        assert results
        # Third patient not inserted into MPI, no match
        third = patients[2]
        (pat3, per3, results, prediction) = link.link_record_against_mpi(third, session, default_algorithm, persist=False)
        assert prediction == "no_match"
        assert pat3 is None
        assert per3 is None
        assert not results

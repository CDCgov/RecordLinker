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

from recordlinker import schemas
from recordlinker.hl7 import fhir
from recordlinker.linking import link


class TestInvokeEvaluator:
    def test_with_override(self):
        evaluator = schemas.Evaluator(
            feature="FIRST_NAME",
            func="COMPARE_PROBABILISTIC_FUZZY_MATCH",
            fuzzy_match_threshold=0.5,
            fuzzy_match_measure="Levenshtein",
        )
        rec = schemas.PIIRecord(name=[{"given": ["John"], "family": "Doe"}])
        mpi_rec = schemas.PIIRecord(name=[{"given": ["Jon"], "family": "Doe"}])
        context = schemas.AlgorithmContext(
            log_odds=[
                {"feature": "FIRST_NAME", "value": 10},
            ],
            advanced={
                "fuzzy_match_threshold": 0.9,
                "fuzzy_match_measure": "JaroWinkler",
            },
        )

        result, _ = link.invoke_evaluator(evaluator, rec, mpi_rec, context)
        assert result == 7.5

    def test_with_default(self):
        evaluator = schemas.Evaluator(
            feature="FIRST_NAME",
            func="COMPARE_PROBABILISTIC_FUZZY_MATCH",
        )
        rec = schemas.PIIRecord(name=[{"given": ["John"], "family": "Doe"}])
        mpi_rec = schemas.PIIRecord(name=[{"given": ["Jon"], "family": "Doe"}])
        context = schemas.AlgorithmContext(
            log_odds=[
                {"feature": "FIRST_NAME", "value": 10},
            ],
            advanced={
                "fuzzy_match_threshold": 0.9,
                "fuzzy_match_measure": "JaroWinkler",
            },
        )

        result, _ = link.invoke_evaluator(evaluator, rec, mpi_rec, context)
        assert pytest.approx(result, 0.01) == 9.33


class TestCompare:
    def test_compare_match_worthy_score(self):
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
        mpi_rec = schemas.PIIRecord(
            **{
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
            {"feature": "FIRST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"},
            {"feature": "LAST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"},
        ]
        algorithm_pass = schemas.AlgorithmPass(
            label="pass",
            blocking_keys=["BIRTHDATE"],
            evaluators=evaluators,
            possible_match_window=(0.8, 0.925),
        )
        context = schemas.AlgorithmContext(
            log_odds=[
                {"feature": "FIRST_NAME", "value": 6.85},
                {"feature": "LAST_NAME", "value": 6.35},
            ]
        )

        res, feature_scores = link.compare(rec, mpi_rec, algorithm_pass, context)
        assert round(res, 3) == 12.830
        assert feature_scores["FIRST_NAME"] == 6.85
        assert round(feature_scores["LAST_NAME"], 3) == 5.980

    def test_compare_non_match_worthy_score(self):
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
        mpi_rec = schemas.PIIRecord(
            **{
                "name": [
                    {
                        "given": [
                            "Jan",
                        ],
                        "family": "Dortmunder",
                    }
                ]
            }
        )
        evaluators = [
            {"feature": "FIRST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"},
            {"feature": "LAST_NAME", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"},
        ]
        algorithm_pass = schemas.AlgorithmPass(
            label="pass",
            blocking_keys=["BIRTHDATE"],
            evaluators=evaluators,
            possible_match_window=(0.8, 0.925),
        )
        context = schemas.AlgorithmContext(
            log_odds=[
                {"feature": "FIRST_NAME", "value": 6.85},
                {"feature": "LAST_NAME", "value": 6.35},
            ],
            advanced={"fuzzy_match_threshold": 0.7},
        )

        res, feature_scores = link.compare(rec, mpi_rec, algorithm_pass, context)
        assert round(res, 3) == 5.137
        assert feature_scores["LAST_NAME"] == 0.0
        assert round(feature_scores["FIRST_NAME"], 3) == 5.137

    def test_compare_identifier_match(self):
        rec = schemas.PIIRecord(
            **{
                "identifiers": [
                    {"type": "MR", "authority": "CA", "value": "123456789"},
                    {"type": "SS", "authority": "VA", "value": "987-65-4321"},
                ]
            }
        )
        mpi_rec = schemas.PIIRecord(
            **{
                "identifiers": [
                    {"type": "MR", "authority": "CA", "value": "123456789"},
                    {"type": "SS", "authority": "VA", "value": "987-65-4321"},
                ]
            }
        )

        evaluators = [{"feature": "IDENTIFIER", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"}]

        algorithm_pass = schemas.AlgorithmPass(
            label="pass",
            blocking_keys=["BIRTHDATE"],
            evaluators=evaluators,
            possible_match_window=(0.8, 0.925),
        )
        context = schemas.AlgorithmContext(
            log_odds=[
                {"feature": "IDENTIFIER", "value": 0.35},
            ]
        )

        res, feature_scores = link.compare(rec, mpi_rec, algorithm_pass, context)
        assert res == 0.35
        assert feature_scores == {"IDENTIFIER": 0.35}

    def test_compare_identifier_with_suffix(self):
        rec = schemas.PIIRecord(
            **{
                "identifiers": [
                    {"type": "MR", "authority": "CA", "value": "123456789"},
                    {"type": "SS", "authority": "VA", "value": "111-11-1111"},
                ]
            }
        )
        mpi_rec = schemas.PIIRecord(
            **{
                "identifiers": [
                    {"type": "MR", "authority": "CA", "value": "123456789"},
                    {"type": "SS", "authority": "VA", "value": "987-65-4321"},
                ]
            }
        )

        evaluators = [{"feature": "IDENTIFIER", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"}]
        algorithm_pass = schemas.AlgorithmPass(
            label="pass",
            blocking_keys=["BIRTHDATE"],
            evaluators=evaluators,
            possible_match_window=(0.8, 0.925),
        )
        context = schemas.AlgorithmContext(
            log_odds=[
                {"feature": "IDENTIFIER", "value": 0.35},
            ]
        )

        # should pass as MR is the same for both
        res, feature_scores = link.compare(rec, mpi_rec, algorithm_pass, context)
        assert res == 0.35
        assert feature_scores == {"IDENTIFIER": 0.35}

        algorithm_pass = schemas.AlgorithmPass(
            label="pass",
            blocking_keys=["BIRTHDATE"],
            evaluators=[{"feature": "IDENTIFIER:SS", "func": "COMPARE_PROBABILISTIC_FUZZY_MATCH"}],
            possible_match_window=(0.8, 0.925),
        )
        # should fail as SS is different for both
        res, feature_scores = link.compare(rec, mpi_rec, algorithm_pass, context)
        assert res == 0.0
        assert feature_scores == {"IDENTIFIER:SS": 0.0}


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
        all_results = []
        for data in patients[:2]:
            (_, person, results, _) = link.link_record_against_mpi(data, session, default_algorithm)
            matches.append(bool(person and results))
            all_results.append(results)
            mapped_patients[person.reference_id] += 1

        # First patient inserted into empty MPI, no match
        # Second patient blocks with first patient in first pass, then fuzzy matches name
        assert matches == [False, True]
        assert sorted(list(mapped_patients.values())) == [2]
        # Median contributions don't exist when matches aren't found
        assert all_results[0] == []
        # They do exist for the second fuzzy match though
        assert round(all_results[1][0].median_features["FIRST_NAME"], 3) == 6.393
        assert round(all_results[1][0].median_features["LAST_NAME"], 3) == 6.351

    def test_default_match_two(self, session, default_algorithm, patients):
        matches: list[bool] = []
        matching_passes: list[int] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        all_results = []
        for data in patients:
            (_, person, results, _) = link.link_record_against_mpi(data, session, default_algorithm)
            made_match = bool(person and results)
            matches.append(made_match)
            all_results.append(results)
            if made_match:
                matching_passes.append(results[0].pass_label)

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
        assert matching_passes == [
            "BLOCK_birthdate_identifier_sex_MATCH_first_name_last_name",
            "BLOCK_zip_first_name_last_name_sex_MATCH_address_birthdate",
        ]
        assert sorted(list(mapped_patients.values())) == [1, 1, 1, 3]
        # Median contributions shouldn't exist for any patients that didn't match
        assert all_results[0] == []
        assert all_results[2] == []
        assert all_results[4] == []
        assert all_results[5] == []
        # The records that did match will have scaled medians
        assert round(all_results[1][0].median_features["FIRST_NAME"], 3) == 6.393
        assert round(all_results[1][0].median_features["LAST_NAME"], 3) == 6.351
        assert round(all_results[3][0].median_features["ADDRESS"], 3) == 8.438
        assert round(all_results[3][0].median_features["BIRTHDATE"], 3) == 10.127

    def test_default_match_three(
        self, session, default_algorithm, patients: list[schemas.PIIRecord]
    ):
        # add an additional patient that will fuzzy match to patient 0
        patient0_copy = copy.deepcopy(patients[0])
        patient0_copy.external_id = str(uuid.uuid4())
        patient0_copy.name[0].given[0] = "Jhon"
        patients.append(patient0_copy)
        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        all_results = []
        for data in patients:
            (_, person, results, _) = link.link_record_against_mpi(data, session, default_algorithm)
            matches.append(bool(person and results))
            all_results.append(results)
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
        # Only the newly duplicated patient is one we haven't already checked in another test
        assert round(all_results[6][0].median_features["FIRST_NAME"], 3) == 6.336
        assert round(all_results[6][0].median_features["LAST_NAME"], 3) == 6.351

    def test_match_with_certain_first_pass(
        self, session, default_algorithm, patients: list[schemas.PIIRecord]
    ):
        patients = [patients[0]] + [patients[2]]
        new_record = copy.deepcopy(patients[0])

        # To get certain in pass 1, less than certain in pass 2,
        # need equal DOB, Identifier, First, and Last Name, but wrong address
        new_record.address[0].line[0] = "4444 Different Street"
        patients.append(new_record)

        algorithm = copy.deepcopy(default_algorithm)
        # Need to decrease MMT for example purposes so pass 2 grades
        # as possible
        algorithm.passes[1].possible_match_window = [0.4, 0.9]

        matches: list[bool] = []
        results = []
        for data in patients:
            (_, person, result, _) = link.link_record_against_mpi(data, session, algorithm)
            matches.append(bool(person and result))
            results.append(result)

        assert matches == [False, False, True]
        assert results[2][0].match_grade == "certain"
        assert (
            results[2][0].pass_label == "BLOCK_birthdate_identifier_sex_MATCH_first_name_last_name"
        )

    def test_match_change_in_second_pass(
        self, session, default_algorithm, patients: list[schemas.PIIRecord]
    ):
        patients = [patients[0]] + [patients[2]]
        new_record = copy.deepcopy(patients[0])

        # To get non-certain in pass 1, then certain in pass 2,
        # need equal DOB, Identifier, and Address, and different
        # First and Last Names after first 4 chars
        new_record.name[0].family = "Shepley"
        patients.append(new_record)

        algorithm = copy.deepcopy(default_algorithm)
        # Need to decrease MMT for example purposes so pass 1 grades
        # as possible
        algorithm.passes[0].possible_match_window = [0.4, 0.9]

        matches: list[bool] = []
        results = []
        for data in patients:
            (_, person, result, _) = link.link_record_against_mpi(data, session, algorithm)
            matches.append(bool(person and result))
            results.append(result)

        assert matches == [False, False, True]
        assert results[2][0].match_grade == "certain"
        assert (
            results[2][0].pass_label == "BLOCK_zip_first_name_last_name_sex_MATCH_address_birthdate"
        )

    def test_match_with_missing_field(
        self, session, default_algorithm, patients: list[schemas.PIIRecord]
    ):
        # Make a deep copy of the first patient, then delete some info
        patients = [patients[0]]
        duplicate = copy.deepcopy(patients[0])
        duplicate.external_id = str(uuid.uuid4())
        duplicate.name[0].family = ""
        duplicate.address[0].line[0] = ""
        patients.append(duplicate)

        algorithm = copy.deepcopy(default_algorithm)
        # Test whether we can successfully make a match if info is missing
        algorithm.passes[0].possible_match_window = [0.7, 0.75]
        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        all_results = []
        for data in patients[:2]:
            (_, person, results, _) = link.link_record_against_mpi(data, session, algorithm)
            matches.append(bool(person and results))
            all_results.append(results)
            mapped_patients[person.reference_id] += 1

        # First patient inserted into empty MPI, no match
        # Second patient blocks in each pass, is missing a field, but is allowed to match
        assert matches == [False, True]
        assert sorted(list(mapped_patients.values())) == [2]
        # Test whether we correctly catch a missing feature score in medians
        assert round(all_results[1][0].median_features["FIRST_NAME"], 3) == 6.849
        assert round(all_results[1][0].median_features["LAST_NAME"], 3) == 3.175

    def test_reject_too_many_missing_field(
        self, session, default_algorithm, patients: list[schemas.PIIRecord]
    ):
        # Make a deep copy of the first patient, then delete some info
        patients = [patients[0]]
        duplicate = copy.deepcopy(patients[0])
        duplicate.external_id = str(uuid.uuid4())
        duplicate.name[0].given[0] = ""
        duplicate.address[0].line[0] = ""
        patients.append(duplicate)

        algorithm = copy.deepcopy(default_algorithm)
        # Test whether too many missing points causes failure
        algorithm.algorithm_context.advanced.max_missing_allowed_proportion = 0.3
        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        all_results = []
        for data in patients[:2]:
            (_, person, results, _) = link.link_record_against_mpi(data, session, algorithm)
            matches.append(bool(person and results))
            mapped_patients[person.reference_id] += 1
            all_results.append(results)

        # First patient inserted into empty MPI, no match
        # Second patient blocks in each pass but missing too much data, fails
        assert matches == [False, False]
        # Too much missingness means no match results, should mean no medians
        assert all_results == [[], []]

    def test_both_missingness_params_zero(
        self, session, default_algorithm, patients: list[schemas.PIIRecord]
    ):
        # Make a deep copy of the first patient, then delete some info so
        # that both blocks contain missing fields
        patients = [patients[0]]
        duplicate = copy.deepcopy(patients[0])
        duplicate.external_id = str(uuid.uuid4())
        duplicate.name[0].given[0] = ""
        duplicate.address[0].line[0] = ""
        patients.append(duplicate)

        algorithm = copy.deepcopy(default_algorithm)
        # We'll test lower log-odds cutoffs and show that even if a record
        # would regularly have the points to match, it's disqualified if it
        # violates the user missingness constraint.
        algorithm.algorithm_context.advanced.max_missing_allowed_proportion = 0.0
        algorithm.algorithm_context.advanced.missing_field_points_proportion = 0.0
        algorithm.passes[0].possible_match_window = [0.2, 0.3]
        algorithm.passes[1].possible_match_window = [0.2, 0.3]
        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        for data in patients[:2]:
            (_, person, results, _) = link.link_record_against_mpi(data, session, algorithm)
            matches.append(bool(person and results))
            mapped_patients[person.reference_id] += 1

        # First patient inserted into empty MPI, no match
        # Second patient blocks in each pass, has score to match, but missingness
        # disqualifies it
        assert matches == [False, False]

    def test_missing_field_points_exceed_max_missingness_fraction(
        self, session, default_algorithm, patients: list[schemas.PIIRecord]
    ):
        """
        Tests for the edge case where missing_field_points_proportion is large
        but max_missing_allowed_proportion is small. This could easily result
        from a situation where a user trains an algorithm that has a number of
        low-log-odds-weight fields (e.g. lots of points 2 or fewer) that they
        don't wish to ignore, but they still want their comparison to be between
        mostly complete records, e.g. not allowing more than 10% of field points
        to be missing.
        """
        # Make a deep copy of the first patient, then delete some info
        patients = [patients[0]]
        duplicate = copy.deepcopy(patients[0])
        duplicate.external_id = str(uuid.uuid4())
        duplicate.name[0].given[0] = ""
        duplicate.address[0].line[0] = ""
        patients.append(duplicate)

        algorithm = copy.deepcopy(default_algorithm)
        # Create scenario described above: each pass will have 10 total points,
        # the missing field will represent a small number of these points, but
        # the total result should still be disqualified
        log_odds = [
            {"feature": "FIRST_NAME", "log_odds": 2.5},
            {"feature": "LAST_NAME", "log_odds": 7.5},
            {"feature": "BIRTHDATE", "log_odds": 7.5},
            {"feature": "ADDRESS", "log_odds": 2.5},
        ]
        algorithm.algorithm_context.advanced.max_missing_allowed_proportion = 0.2
        algorithm.algorithm_context.advanced.missing_field_points_proportion = 0.7
        algorithm.algorithm_context.log_odds = log_odds
        algorithm.passes[0].possible_match_window = [0.7, 0.8]
        algorithm.passes[1].possible_match_window = [0.7, 0.8]
        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        for data in patients[:2]:
            (_, person, results, _) = link.link_record_against_mpi(data, session, algorithm)
            matches.append(bool(person and results))
            mapped_patients[person.reference_id] += 1

        # First patient inserted into empty MPI, no match
        # Second patient blocks in each pass, only gets a tiny bump overall from
        # low-value missing field, but fails user's overall completeness constraint
        assert matches == [False, False]

    def test_no_match_one_suffix_one_not(
        self, session, default_algorithm, patients: list[schemas.PIIRecord]
    ):
        # Make a deep copy of the first patient, give it a suffix
        patients = [patients[0]]
        duplicate = copy.deepcopy(patients[0])
        duplicate.external_id = str(uuid.uuid4())
        duplicate.name[0].suffix = ["Sr"]
        patients.append(duplicate)

        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        for data in patients[:2]:
            (_, person, results, _) = link.link_record_against_mpi(data, session, default_algorithm)
            matches.append(bool(person and results))
            mapped_patients[person.reference_id] += 1

        # First patient inserted into empty MPI, no match
        # Second patient fails eval in first pass and blocking in second
        # due to suffix
        assert matches == [False, False]

    def test_no_match_same_name_diff_suffixes(
        self, session, default_algorithm, patients: list[schemas.PIIRecord]
    ):
        """
        NOTE: This catches the Jr/Sr edge case of a parent and child
        living at the same address with the same first name. It even
        goes a step farther and gives them the same birthday.
        """
        # Give both patients the same name before duplication, change
        # suffixes after
        patients = [patients[0]]
        duplicate = copy.deepcopy(patients[0])
        patients[0].name[0].suffix = ["Sr"]
        duplicate.external_id = str(uuid.uuid4())
        duplicate.name[0].suffix = ["Jr"]
        patients.append(duplicate)

        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        for data in patients[:2]:
            (_, person, results, _) = link.link_record_against_mpi(data, session, default_algorithm)
            matches.append(bool(person and results))
            mapped_patients[person.reference_id] += 1

        # First patient inserted into empty MPI, no match
        # Second patient fails eval in first pass and blocking in second
        # due to suffix being different
        assert matches == [False, False]

    def test_no_match_diff_names_same_suffix(
        self, session, default_algorithm, patients: list[schemas.PIIRecord]
    ):
        # Give each copy the same suffix, duplicate, then change name
        patients = [patients[0]]
        patients[0].name[0].suffix = ["Sr"]
        duplicate = copy.deepcopy(patients[0])
        duplicate.external_id = str(uuid.uuid4())
        duplicate.name[0].given[0] = "Jason"
        patients.append(duplicate)

        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        for data in patients[:2]:
            (_, person, results, _) = link.link_record_against_mpi(data, session, default_algorithm)
            matches.append(bool(person and results))
            mapped_patients[person.reference_id] += 1

        # First patient inserted into empty MPI, no match
        # Second patient fails eval in first pass and blocking in second
        # due to suffix
        assert matches == [False, False]

    def test_match_name_with_suffix(
        self, session, default_algorithm, patients: list[schemas.PIIRecord]
    ):
        # Give patient a suffix, duplicate, then introduce a small typo
        # to make sure we can fuzzy match it still
        patients = [patients[0]]
        patients[0].name[0].suffix = ["Sr"]
        duplicate = copy.deepcopy(patients[0])
        duplicate.external_id = str(uuid.uuid4())
        duplicate.name[0].given[0] = "Jon"
        patients.append(duplicate)

        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        for data in patients[:2]:
            (_, person, results, _) = link.link_record_against_mpi(data, session, default_algorithm)
            matches.append(bool(person and results))
            mapped_patients[person.reference_id] += 1

        # First patient inserted into empty MPI, no match
        # Second patient blocks in first pass, then passes evaluation, match
        assert matches == [False, True]

    def test_default_possible_match(
        self, session, default_algorithm, possible_match_default_patients: list[schemas.PIIRecord]
    ):
        match_grades: dict[str, dict] = collections.defaultdict(dict)
        # Can just set the threshold for certainty higher to catch a possible match
        default_algorithm.passes[0].possible_match_window = (0.7, 0.95)
        for i, data in enumerate(possible_match_default_patients):
            (patient, person, results, match_grade) = link.link_record_against_mpi(
                data, session, default_algorithm
            )
            match_grades[i] = {
                "patient": patient,
                "person": person,
                "results": results,
                "match_grade": match_grade,
            }

        # We'll have one match_grade of each type, matched in the order
        # certainly-not, certain, possible
        assert match_grades[0]["match_grade"] == "certainly-not"
        assert match_grades[1]["match_grade"] == "certain"
        assert match_grades[2]["match_grade"] == "possible"
        assert match_grades[2]["results"][0].person == match_grades[0]["person"]
        assert (
            match_grades[2]["results"][0].rms
            >= default_algorithm.passes[0].possible_match_window[0]
        )
        assert (
            match_grades[2]["results"][0].rms < default_algorithm.passes[0].possible_match_window[1]
        )

    def test_include_multiple_matches_true(
        self, session, default_algorithm, multiple_matches_patients: list[schemas.PIIRecord]
    ):
        match_grades: dict[str, dict] = collections.defaultdict(dict)
        for i, data in enumerate(multiple_matches_patients):
            (patient, person, results, match_grade) = link.link_record_against_mpi(
                data, session, default_algorithm
            )
            match_grades[i] = {
                "patient": patient,
                "person": person,
                "results": results,
                "match_grade": match_grade,
            }

        # We'll have four match_grades: two 'certainly-not' followed by
        # two 'certain'
        assert match_grades[0]["match_grade"] == "certainly-not"
        assert match_grades[1]["match_grade"] == "certainly-not"
        assert match_grades[2]["match_grade"] == "certain"
        assert match_grades[3]["match_grade"] == "certain"

        # The first 'certain' match is a 'Johnathan' matching to both a
        # 'John' and a 'Jonathan' using different grades in different passes
        assert len(match_grades[2]["results"]) == 2
        for match in match_grades[2]["results"]:
            assert match.rms >= match.cmt

        # Since grades are the same, assign final match to one with higher RMS (1.0)
        assert match_grades[2]["person"] == match_grades[0]["person"]
        assert match_grades[2]["results"][0].rms == 1.0

    def test_include_multiple_matches_false(
        self, session, default_algorithm, multiple_matches_patients: list[schemas.PIIRecord]
    ):
        match_grades: dict[str, dict] = collections.defaultdict(dict)
        default_algorithm.algorithm_context.include_multiple_matches = False
        for i, data in enumerate(multiple_matches_patients):
            (patient, person, results, match_grade) = link.link_record_against_mpi(
                data, session, default_algorithm
            )
            match_grades[i] = {
                "patient": patient,
                "person": person,
                "results": results,
                "match_grade": match_grade,
            }

        # The match cases are as above, but we only include 1 result
        assert len(match_grades[2]["results"]) == 1
        assert match_grades[2]["match_grade"] == "certain"
        assert match_grades[2]["results"][0].rms >= match_grades[2]["results"][0].cmt
        assert match_grades[2]["person"] == match_grades[0]["person"]

    def test_no_persist(self, session, default_algorithm, patients):
        # First patient inserted into MPI, no match
        first = patients[0]
        (pat1, per1, results, match_grade) = link.link_record_against_mpi(
            first, session, default_algorithm, persist=True
        )
        assert match_grade == "certainly-not"
        assert pat1 is not None
        assert per1 is not None
        assert not results
        # Second patient not inserted into MPI, match first person
        second = patients[1]
        (pat2, per2, results, match_grade) = link.link_record_against_mpi(
            second, session, default_algorithm, persist=False
        )
        assert match_grade == "certain"
        assert pat2 is None
        assert per2 is not None
        assert per2.reference_id == per1.reference_id
        assert results
        # Third patient not inserted into MPI, no match
        third = patients[2]
        (pat3, per3, results, match_grade) = link.link_record_against_mpi(
            third, session, default_algorithm, persist=False
        )
        assert match_grade == "certainly-not"
        assert pat3 is None
        assert per3 is None
        assert not results

"""
unit.linking.test_link.py
~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.linking.link module.
"""

import collections
import copy
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy import orm

from recordlinker import models
from recordlinker import utils
from recordlinker.config import settings
from recordlinker.linking import link
from recordlinker.linking import matchers


@pytest.fixture(scope="function")
def session():
    engine = create_engine(settings.test_db_uri)
    models.Base.metadata.create_all(engine)  # Create all tables in the in-memory database

    # Create a new session factory and scoped session
    Session = orm.scoped_session(orm.sessionmaker(bind=engine))
    session = Session()

    yield session  # This is where the testing happens

    session.close()  # Cleanup after test
    models.Base.metadata.drop_all(engine)  # Drop all tables after the test


class TestCompare:
    def test_compare_match(self):
        rec = models.PIIRecord(
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
        linkage_pass = {
            "funcs": {
                "first_name": matchers.feature_match_exact,
                "last_name": matchers.feature_match_fuzzy_string,
            },
            "matching_rule": matchers.eval_perfect_match,
        }
        assert link.compare(rec, pat, linkage_pass) is True

    def test_compare_no_match(self):
        rec = models.PIIRecord(
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
        linkage_pass = {
            "funcs": {
                "first_name": matchers.feature_match_exact,
                "last_name": matchers.feature_match_exact,
            },
            "matching_rule": matchers.eval_perfect_match,
        }
        assert link.compare(rec, pat, linkage_pass) is False


class TestLinkRecordAgainstMpi:
    @pytest.fixture
    def basic_algorithm(self):
        return utils.read_json_from_assets("linking", "basic_algorithm.json")["algorithm"]

    @pytest.fixture
    def enhanced_algorithm(self):
        return utils.read_json_from_assets("linking", "enhanced_algorithm.json")["algorithm"]

    @pytest.fixture
    def patients(self):
        bundle = utils.read_json_from_assets("linkage", "patient_bundle_to_link_with_mpi.json")
        patients = []
        for entry in bundle["entry"]:
            if entry.get("resource", {}).get("resourceType", {}) == "Patient":
                patients.append(entry["resource"])
        return patients

    def test_basic_match_one(self, session, basic_algorithm, patients):
        # Test various null data values in incoming record
        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        for idx, patient in enumerate(patients[:2]):
            matched, pid = link.link_record_against_mpi(patient, session, basic_algorithm)
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
            matched, pid = link.link_record_against_mpi(patient, session, basic_algorithm)
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

    def test_enhanced_match_three(self, session, enhanced_algorithm, patients):
        # add an additional patient that will fuzzy match to patient 0
        patient0_copy = copy.deepcopy(patients[0])
        patient0_copy["id"] = str(uuid.uuid4())
        patient0_copy["name"][0]["given"][0] = "Jhon"
        patients.append(patient0_copy)
        matches: list[bool] = []
        mapped_patients: dict[str, int] = collections.defaultdict(int)
        for patient in patients:
            matched, pid = link.link_record_against_mpi(patient, session, enhanced_algorithm)
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

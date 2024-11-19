"""
unit.test_matchers
~~~~~~~~~~~~~~~~~~

This module contains unit tests for the :mod:`~recordlinker.linkage.matchers` module.
"""

import datetime

import pytest

from recordlinker.linking import old_matchers as matchers


def test_get_fuzzy_params():
    kwargs = {
        "similarity_measure": "Levenshtein",
        "thresholds": {"city": 0.95, "address": 0.98},
    }

    assert matchers._get_fuzzy_params("city", **kwargs) == ("Levenshtein", 0.95)
    assert matchers._get_fuzzy_params("address", **kwargs) == ("Levenshtein", 0.98)
    assert matchers._get_fuzzy_params("first_name", **kwargs) == ("Levenshtein", 0.7)

    del kwargs["similarity_measure"]

    assert matchers._get_fuzzy_params("last_name", **kwargs) == ("JaroWinkler", 0.7)


def test_fuzzy_match():
    record_i = ["string1", "John", "John", "1985-12-12", None]
    record_j = ["string2", "Jhon", "Jon", "1985-12-12", None]

    cols = {"col_1": 0, "col_2": 1, "col_3": 2, "col_4": 3}

    for c in cols:
        assert matchers.fuzzy_match(
            record_i,
            record_j,
            c,
            cols,
            similarity_measure="JaroWinkler",
            threshold=0.7,
        )
    assert not matchers.fuzzy_match(
        ["no match"],
        ["dont match me bro"],
        "col_5",
        {"col_5": 0},
        similarity_measure="JaroWinkler",
        threshold=0.7,
    )


def test_match_rule():
    assert matchers.match_rule([1, 1, 1])
    assert not matchers.match_rule([1, 1, 0])
    assert not matchers.match_rule([1, 0, 0])
    assert not matchers.match_rule([0, 0, 0])


def test_match_within_block_cluster_ratio():
    data = [
        [1, "John", "Shepard", "11-7-2153", "90909"],
        [5, "Jhon", "Sheperd", "11-7-2153", "90909"],
        [11, "Jon", "Shepherd", "11-7-2153", "90909"],
        [12, "Johnathan", "Shepard", "11-7-2153", "90909"],
        [13, "Nathan", "Shepard", "11-7-2153", "90909"],
        [14, "Jane", "Smith", "01-10-1986", "12345"],
        [18, "Daphne", "Walker", "12-12-1992", "23456"],
        [23, "Alejandro", "Villanueve", "1-1-1980", "15935"],
        [24, "Alejandro", "Villanueva", "1-1-1980", "15935"],
        [27, "Philip", "", "2-2-1990", "64873"],
        [31, "Alejandr", "Villanueve", "1-1-1980", "15935"],
        [32, "Aelxdrano", "Villanueve", "1-1-1980", "15935"],
    ]

    eval_rule = matchers.match_rule
    funcs = {
        "first_name": matchers.fuzzy_match,
        "last_name": matchers.fuzzy_match,
        "birthdate": matchers.exact_match_all,
        "zip": matchers.exact_match_all,
    }
    col_to_idx = {"first_name": 1, "last_name": 2, "birthdate": 3, "zip": 4}

    # Do a test run requiring total membership match
    matches = matchers.match_within_block_cluster_ratio(
        data, 1.0, funcs, col_to_idx, eval_rule, threshold=0.8
    )
    assert matches == [{0, 1, 2}, {3}, {4}, {5}, {6}, {7, 8, 10}, {9}, {11}]

    # Now do a test showing different cluster groupings
    matches = matchers.match_within_block_cluster_ratio(
        data, 0.6, funcs, col_to_idx, eval_rule, threshold=0.8
    )
    assert matches == [{0, 1, 2, 3}, {4}, {5}, {6}, {7, 8, 10, 11}, {9}]


def test_match_within_block():
    # Data will be of the form:
    # patient_id, first_name, last_name, DOB, zip code
    data = [
        [1, "John", "Shepard", "11-7-2153", "90909"],
        [5, "Jhon", "Sheperd", "11-7-2153", "90909"],
        [11, "Jon", "Shepherd", "11-7-2153", "90909"],
        [14, "Jane", "Smith", "01-10-1986", "12345"],
        [18, "Daphne", "Walker", "12-12-1992", "23456"],
        [23, "Alejandro", "Villanueve", "1-1-1980", "15935"],
        [24, "Alejandro", "Villanueva", "1-1-1980", "15935"],
        [27, "Philip", "", "2-2-1990", "64873"],
        [31, "Alejandr", "Villanueve", "1-1-1980", "15935"],
    ]
    eval_rule = matchers.match_rule

    # First, require exact matches on everything to match
    # Expect 0 pairs
    funcs = {
        "first_name": matchers.exact_match_all,
        "last_name": matchers.exact_match_all,
        "birthdate": matchers.exact_match_all,
        "zip": matchers.exact_match_all,
    }
    col_to_idx = {"first_name": 1, "last_name": 2, "birthdate": 3, "zip": 4}
    match_pairs = matchers.match_within_block(data, funcs, col_to_idx, eval_rule)
    assert len(match_pairs) == 0

    # Now, require exact on DOB and zip, but allow fuzzy on first and last
    # Expect 6 matches
    funcs["first_name"] = matchers.fuzzy_match
    funcs["last_name"] = matchers.fuzzy_match
    match_pairs = matchers.match_within_block(data, funcs, col_to_idx, eval_rule)
    assert match_pairs == [(0, 1), (0, 2), (1, 2), (5, 6), (5, 8), (6, 8)]

    # As above, but let's be explicit about string comparison and threshold
    # Expect three matches, but none with the "Johns"
    # Note the difference in returned results by changing distance function
    match_pairs = matchers.match_within_block(
        data,
        funcs,
        col_to_idx,
        eval_rule,
        similarity_measure="Levenshtein",
        threshold=0.8,
    )
    assert match_pairs == [(5, 6), (5, 8), (6, 8)]


def test_feature_match_four_char():
    record_i = ["Johnathan", "Shepard"]
    record_j = ["John", "Sheperd"]
    record_k = ["Jhon", "Sehpard"]

    cols = {"first": 0, "last": 1}

    # Simultaneously test matches and non-matches of different data types
    for c in cols:
        assert matchers.feature_match_four_char(record_i, record_j, c, cols)
        assert not matchers.feature_match_four_char(record_i, record_k, c, cols)


def test_exact_match_all():
    record_i = [
        "240 Rippin Ranch Apt 66",
        "1980-01-01",
        "Los Angeles",
        "Verónica Eva",
        "Reynoso",
        "834d436b-9e1f-2e8e-f28a-ad40bef9f365",
        "female",
        "CA",
        "90502",
    ]
    record_j = [
        "240 Rippin Ranch Apt 66",
        "1980-01-01",
        "Los Angeles",
        "Verónica Eva",
        "Reynoso",
        "834d436b-9e1f-2e8e-f28a-ad40bef9f365",
        "female",
        "CA",
        "90502",
    ]
    record_k = [
        "240 Rippin Ranch Apt 66",
        datetime.date(1980, 1, 1),
        "Los Angeles",
        "Verónica Eva",
        "Reynoso",
        "834d436b-9e1f-2e8e-f28a-ad40bef9f365",
        "female",
        "CA",
        "90502",
    ]
    record_l = [
        "123 X St Unit 2",
        "1995-06-20",
        "Chicago",
        "Alejandra",
        "Arenas",
        "124d436b-9e1f-2e8e-f28a-ad40bef9f367",
        "male",
        "IL",
        "60615",
    ]
    record_m = [
        "123 X St Unit 2",
        datetime.date(1980, 6, 20),
        "Chicago",
        "Alejandra",
        "Arenas",
        "124d436b-9e1f-2e8e-f28a-ad40bef9f367",
        "male",
        "IL",
        "60615",
    ]

    cols = {
        "address": 0,
        "birthdate": 1,
        "city": 2,
        "first_name": 3,
        "last_name": 4,
        "mrn": 5,
        "sex": 6,
        "state": 7,
        "zip": 8,
    }

    # Simultaneously test matches and non-matches of different data types
    for c in cols:
        assert matchers.exact_match_all(record_i, record_j, c, cols)
        assert matchers.exact_match_all(record_i, record_k, c, cols)
        assert not matchers.exact_match_all(record_i, record_l, c, cols)
        assert not matchers.exact_match_all(record_i, record_m, c, cols)

    # Special case for matching None--None == None is vacuous
    assert matchers.exact_match_all([None], [None], "col_7", {"col_7": 0})


def test_probabilistic_match_rule():
    with pytest.raises(KeyError) as e:
        matchers.probabilistic_match_rule([])
    assert "Cutoff threshold for true matches must be passed" in str(e.value)

    assert not matchers.probabilistic_match_rule([], true_match_threshold=10.0)
    assert not matchers.probabilistic_match_rule([1.0, 0.0, 6.0, 2.7], true_match_threshold=10.0)
    assert matchers.probabilistic_match_rule([4.3, 6.1, 2.5], true_match_threshold=10.0)


def test_feature_match_log_odds_exact():
    with pytest.raises(KeyError) as e:
        matchers.feature_match_log_odds_exact([], [], "c", {})
    assert "Mapping of columns to m/u log-odds must be provided" in str(e.value)

    ri = ["John", "Shepard", "11-07-1980", "1234 Silversun Strip"]
    rj = ["John", 6.0, None, "2345 Goldmoon Ave."]
    col_to_idx = {"first": 0, "last": 1, "birthdate": 2, "address": 3}
    log_odds = {"first": 4.0, "last": 6.5, "birthdate": 9.8, "address": 3.7}

    assert (
        matchers.feature_match_log_odds_exact(ri, rj, "first", col_to_idx, log_odds=log_odds) == 4.0
    )

    for c in col_to_idx:
        if c != "first":
            assert (
                matchers.feature_match_log_odds_exact(ri, rj, c, col_to_idx, log_odds=log_odds)
                == 0.0
            )

import pytest
from conftest import load_test_json_asset

from recordlinker.linking.skip_values import remove_skip_values
from recordlinker.schemas.pii import PIIRecord
from recordlinker.tuning.prob_calc import _compare_records_in_pair
from recordlinker.tuning.prob_calc import _score_pairs_in_class
from recordlinker.tuning.prob_calc import calculate_and_sort_tuning_scores
from recordlinker.tuning.prob_calc import calculate_class_probs
from recordlinker.tuning.prob_calc import calculate_log_odds
from recordlinker.tuning.prob_calc import estimate_rms_bounds


class TestTuningProbabilityCalculators:
    def test_calculate_class_probs_m(self):
        test_pairs = load_test_json_asset("synthetic_tuning_pairs.json")
        rows = []
        for p in test_pairs["samples"]:
            row = (p["data_1"], p["data_2"])
            rows.append(row)
        m_probs = calculate_class_probs(rows)
        assert m_probs == {
            'BIRTHDATE': (2.0 / 3.0),
            'SEX': (5.0 / 6.0),
            'FIRST_NAME': (5.0 / 6.0),
            'LAST_NAME': 1.0,
            'ADDRESS': 1.0,
            'CITY': (2.0 / 3.0),
            'STATE': 1.0,
            'ZIP': (5.0 / 6.0),
            'RACE': 1.0,
            'TELECOM': 1.0,
            'PHONE': 1.0,
            'EMAIL': (1.0 / 6.0),
            'COUNTY': 1.0,
            'IDENTIFIER': 1.0
        }

    def test_calculate_class_probs_u(self):
        test_pairs = load_test_json_asset("synthetic_tuning_pairs.json")
        # Pairs come matched up as true-class examples, so just move the
        # second record in each pair up by one to make them all non-match
        rows = []
        for i in range(len(test_pairs["samples"]) - 1):
            r1 = test_pairs["samples"][i]["data_1"]
            r2 = test_pairs["samples"][i+1]["data_2"]
            rows.append((r1, r2))
        rows.append((
            test_pairs["samples"][len(test_pairs["samples"]) - 1]["data_1"],
            test_pairs["samples"][0]["data_2"]
        ))

        u_probs = calculate_class_probs(rows)
        assert u_probs == {
            'BIRTHDATE': (1.0 / 6.0),
            'SEX': (1.0 / 3.0),
            'FIRST_NAME': (1.0 / 6.0),
            'LAST_NAME': (1.0 / 6.0),
            'ADDRESS': (1.0 / 6.0),
            'CITY': (1.0 / 6.0),
            'STATE': (1.0 / 3.0),
            'ZIP': (1.0 / 6.0),
            'RACE': (1.0 / 3.0),
            'TELECOM': (1.0 / 6.0),
            'PHONE': (1.0 / 6.0),
            'EMAIL': (1.0 / 6.0),
            'COUNTY': (1.0 / 6.0),
            'IDENTIFIER': (1.0 / 6.0)
        }

    def test_calculate_log_odds(self):
        m_probs = {
            'BIRTHDATE': (2.0 / 3.0),
            'SEX': (5.0 / 6.0),
            'FIRST_NAME': (5.0 / 6.0),
            'LAST_NAME': 1.0,
            'ADDRESS': 1.0,
            'CITY': (2.0 / 3.0),
            'STATE': 1.0,
            'ZIP': (5.0 / 6.0),
            'RACE': 1.0,
            'TELECOM': 1.0,
            'PHONE': 1.0,
            'EMAIL': (1.0 / 6.0),
            'COUNTY': 1.0,
            'IDENTIFIER': 1.0
        }

        u_probs = {
            'BIRTHDATE': (1.0 / 6.0),
            'SEX': (1.0 / 3.0),
            'FIRST_NAME': (1.0 / 6.0),
            'LAST_NAME': (1.0 / 6.0),
            'ADDRESS': (1.0 / 6.0),
            'CITY': (1.0 / 6.0),
            'STATE': (1.0 / 3.0),
            'ZIP': (1.0 / 6.0),
            'RACE': (1.0 / 3.0),
            'TELECOM': (1.0 / 6.0),
            'PHONE': (1.0 / 6.0),
            'EMAIL': (1.0 / 6.0),
            'COUNTY': (1.0 / 6.0),
            'IDENTIFIER': (1.0 / 6.0)
        }
        log_odds = calculate_log_odds(m_probs, u_probs)
        assert round(log_odds['BIRTHDATE'], 3) == 1.386
        assert round(log_odds['SEX'], 3) == 0.916
        assert round(log_odds['FIRST_NAME'], 3) == 1.609
        assert round(log_odds['LAST_NAME'], 3) == 1.792
        assert round(log_odds['ADDRESS'], 3) == 1.792
        assert round(log_odds['CITY'], 3) == 1.386
        assert round(log_odds['STATE'], 3) == 1.099
        assert round(log_odds['ZIP'], 3) == 1.609
        assert round(log_odds['RACE'], 3) == 1.099
        assert round(log_odds['TELECOM'], 3) == 1.792
        assert round(log_odds['PHONE'], 3) == 1.792
        assert round(log_odds['EMAIL'], 3) == 0.0
        assert round(log_odds['COUNTY'], 3) == 1.792
        assert round(log_odds['IDENTIFIER'], 3) == 1.792


class TestScoreTuningSamples:
    @pytest.fixture
    def log_odds(self):
        return {
            'BIRTHDATE': 1.386,
            'SEX': 0.916,
            'FIRST_NAME': 1.609,
            'LAST_NAME': 1.792,
            'ADDRESS': 1.792,
            'CITY': 1.386,
            'STATE': 1.099,
            'ZIP': 1.609,
            'RACE': 1.099,
            'TELECOM': 1.792,
            'PHONE': 1.792,
            'EMAIL': 0.0,
            'COUNTY': 1.792,
            'IDENTIFIER': 1.792,
        }
    
    @pytest.fixture
    def true_match_samples(self):
        test_pairs = load_test_json_asset("synthetic_tuning_pairs.json")
        rows = []
        for p in test_pairs["samples"]:
            row = (p["data_1"], p["data_2"])
            rows.append(row)
        return rows
    
    @pytest.fixture
    def non_match_samples(self):
        test_pairs = load_test_json_asset("synthetic_tuning_pairs.json")
        rows = []
        for i in range(len(test_pairs["samples"]) - 1):
            r1 = test_pairs["samples"][i]["data_1"]
            r2 = test_pairs["samples"][i+1]["data_2"]
            rows.append((r1, r2))
        rows.append((
            test_pairs["samples"][len(test_pairs["samples"]) - 1]["data_1"],
            test_pairs["samples"][0]["data_2"]
        ))
        return rows

    def test_compare_records_in_pair(self, default_algorithm, log_odds, true_match_samples, non_match_samples):

        context = default_algorithm.algorithm_context
        pass_1 = default_algorithm.passes[0]
        max_points = sum(
            [log_odds[str(e.feature)] or 0.0 for e in pass_1.evaluators]
        )

        # Run one check of comparisons on a true match pair
        # Fields should all line up, should be max
        pii_record_1 = PIIRecord.from_data(true_match_samples[0][0])
        pii_record_1 = remove_skip_values(pii_record_1, context.skip_values)
        pii_record_2 = PIIRecord.from_data(true_match_samples[0][1])
        pii_record_2 = remove_skip_values(pii_record_2, context.skip_values)
        result = _compare_records_in_pair(pii_record_1, pii_record_2, log_odds, max_points, pass_1, context)
        assert result == 3.401

        # Now run a check of comparisons on a non-match pair
        # Stuff should be missing and wrong so we should get a 0
        pii_record_1 = PIIRecord.from_data(non_match_samples[0][0])
        pii_record_1 = remove_skip_values(pii_record_1, context.skip_values)
        pii_record_2 = PIIRecord.from_data(non_match_samples[0][1])
        pii_record_2 = remove_skip_values(pii_record_2, context.skip_values)
        result = _compare_records_in_pair(pii_record_1, pii_record_2, log_odds, max_points, pass_1, context)
        assert result == 0.0

    def test_score_pairs_in_class(self, default_algorithm, log_odds, true_match_samples, non_match_samples):
        context = default_algorithm.algorithm_context
        for idx, algorithm_pass in enumerate(default_algorithm.passes):
            max_points_in_pass: float = sum(
                [log_odds[str(e.feature)] or 0.0 for e in algorithm_pass.evaluators]
            )
            true_scores = _score_pairs_in_class(true_match_samples, log_odds, max_points_in_pass, algorithm_pass, context)
            true_scores = [round(x, 3) for x in true_scores]
            non_match_scores = _score_pairs_in_class(non_match_samples, log_odds, max_points_in_pass, algorithm_pass, context)
            # Scores for first pass
            if idx == 0:
                assert true_scores == [1.0, 1.0, 1.0, 0.527, 1.0]
                assert non_match_scores == [0.0] * 5
            else:
                assert true_scores == [1.0, 1.0, 0.564, 0.564, 1.0]
                assert non_match_scores == [0.0] * 5
    
    def test_calculate_and_sort_tuning_scores(self, default_algorithm, log_odds, true_match_samples, non_match_samples):
        sorted_scores = calculate_and_sort_tuning_scores(
            true_match_samples, non_match_samples, log_odds, default_algorithm
        )
        true_match_scores, non_match_scores = sorted_scores['BLOCK_birthdate_identifier_sex_MATCH_first_name_last_name']
        true_match_scores = [round(x, 3) for x in true_match_scores]
        assert true_match_scores == [0.527, 1.0, 1.0, 1.0, 1.0]
        assert non_match_scores == [0.0, 0.0, 0.0, 0.0, 0.0]
        true_match_scores, non_match_scores = sorted_scores['BLOCK_zip_first_name_last_name_sex_MATCH_address_birthdate']
        true_match_scores = [round(x, 3) for x in true_match_scores]
        assert true_match_scores == [0.564, 0.564, 1.0, 1.0, 1.0]
        assert non_match_scores == [0.0] * 5

class TestRmsBoundEstimation:
    def test_estimate_rms_no_overlap_no_mmt(self):
        true_match_scores = [0.564, 1.0, 1.0, 1.0, 1.0]
        non_match_scores = [0.0, 0.0, 0.0, 0.05, 0.25]
        sorted_scores = {
            "pass_1": (true_match_scores, non_match_scores)
        }
        suggested_bounds = estimate_rms_bounds(sorted_scores)
        assert suggested_bounds['pass_1'][0] == 0.25
        assert suggested_bounds['pass_1'][1] == 0.589

    def test_estimate_rms_normal_overlap(self):
        true_match_scores = [0.85, 0.92, 0.97, 1.0, 1.0]
        non_match_scores = [0.0, 0.15, 0.33, 0.86, 0.93]
        sorted_scores = {
            "pass_1": (true_match_scores, non_match_scores)
        }
        suggested_bounds = estimate_rms_bounds(sorted_scores)
        assert suggested_bounds['pass_1'][0] == 0.835
        assert suggested_bounds['pass_1'][1] == 0.995

    def test_estimate_rms_skewed_overlap_no_cmt(self):
        true_match_scores = [0.77, 0.78, 0.78, 0.79, 0.81]
        non_match_scores = [0.56, 0.64, 0.67, 0.8, 0.83]
        sorted_scores = {
            "pass_1": (true_match_scores, non_match_scores)
        }
        suggested_bounds = estimate_rms_bounds(sorted_scores)
        assert suggested_bounds['pass_1'][0] == 0.775
        assert suggested_bounds['pass_1'][1] == 0.84

    def test_estimate_rms_multiple_passes(self):
        sorted_scores = {
            'pass_1': (
                [.8, .8, .83, .88, .94], [.1, .2, .3, .3, .435]
            ),
            'pass_2': (
                [.6, .7, .7, .77, .78], [.5, .56, .62, .65, .65]
            )
        }
        suggested_bounds = estimate_rms_bounds(sorted_scores)
        assert suggested_bounds['pass_1'][0] == 0.435
        assert round(suggested_bounds['pass_1'][1], 3) == 0.825
        assert suggested_bounds['pass_2'] == (0.595, 0.725)
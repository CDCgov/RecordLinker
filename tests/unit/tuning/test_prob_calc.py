from conftest import load_test_json_asset

from recordlinker.tuning.prob_calc import calculate_class_probs
from recordlinker.tuning.prob_calc import calculate_log_odds


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
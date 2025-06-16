import math
import typing

from sqlalchemy.engine.row import Row

from recordlinker.linking.matchers import compare_probabilistic_exact_match
from recordlinker.schemas.pii import PIIRecord, FeatureAttribute, Feature

FIELDS_TO_IGNORE = ["GIVEN_NAME", "NAME", "SUFFIX"]
FIELDS_TO_CALCULATE = [Feature.parse(f.value) for f in FeatureAttribute if f.value not in FIELDS_TO_IGNORE]

def calculate_m_probs(true_match_pairs: typing.Sequence[Row]):
    """
    Calculate the class-conditional likelihood that two records will
    agree on a particular field, given that the two records are a
    known true-match.
    """
    # LaPlacian smoothing accounts for unseen instances
    m_probs = {str(f): 1.0 for f in FIELDS_TO_CALCULATE}

    for pair in true_match_pairs:
        pii_record_1 = PIIRecord.from_data(pair[3])
        pii_record_2 = PIIRecord.from_data(pair[4])

        # The probabilistic exact matcher nicely uses feature_iter and
        # cross-value checking for us; if we award 0 points for missing
        # data and 1 point for perfect agreement, we get the count
        for f in FIELDS_TO_CALCULATE:
            comparison = compare_probabilistic_exact_match(
                pii_record_1, pii_record_2, f, 1.0, 0.0, prepend_suffix=False
            )
            m_probs[str(f)] += comparison[0]
    
    for k in m_probs:
        m_probs[k] /= float(len(true_match_pairs) + 1)
    
    return m_probs


def calculate_u_probs(non_match_pairs: typing.Sequence[typing.Tuple]):
    """
    Calculate the class-conditional likelihood that two records will
    agree on a particular field, given that the two records are a
    known non-match.
    """
        # LaPlacian smoothing accounts for unseen instances
    u_probs = {str(f): 1.0 for f in FIELDS_TO_CALCULATE}

    for pair in non_match_pairs:
        pii_record_1 = PIIRecord.from_data(pair[0])
        pii_record_2 = PIIRecord.from_data(pair[1])

        # The probabilistic exact matcher nicely uses feature_iter and
        # cross-value checking for us; if we award 0 points for missing
        # data and 1 point for perfect agreement, we get the count
        for f in FIELDS_TO_CALCULATE:
            comparison = compare_probabilistic_exact_match(
                pii_record_1, pii_record_2, f, 1.0, 0.0, prepend_suffix=False
            )
            u_probs[str(f)] += comparison[0]
    
    for k in u_probs:
        u_probs[k] /= float(len(non_match_pairs) + 1)
    
    return u_probs


def calculate_log_odds(
        m_probs: dict[str, float],
        u_probs: dict[str, float]
    ) -> dict[str, float]:
    """
    Given class-conditional probabilities for field agreement, calculate
    the log-odds values for each field of calculable interest for
    patient matching.
    """
    log_odds = {}
    for field in m_probs:
        log_odds[field] = math.log(m_probs[field] / u_probs[field])
    return log_odds
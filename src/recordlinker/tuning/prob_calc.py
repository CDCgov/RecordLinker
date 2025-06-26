import math
import typing

from recordlinker.linking.matchers import compare_probabilistic_exact_match
from recordlinker.schemas.pii import Feature
from recordlinker.schemas.pii import FeatureAttribute
from recordlinker.schemas.pii import PIIRecord

# We don't need log-odds for every Feature we register, since some
# are folded into other evaluations
FIELDS_TO_IGNORE = ["GIVEN_NAME", "NAME", "SUFFIX"]
FIELDS_TO_CALCULATE = [
    Feature.parse(f.value) for f in FeatureAttribute if f.value not in FIELDS_TO_IGNORE
]

def calculate_class_probs(
        sampled_pairs: typing.Sequence[typing.Tuple[dict, dict]]
    ) -> dict[str, float]:
    """
    Calculate the class-conditional likelihood that two records will
    agree on a particular field, given that the two records are a
    belong to the same class (known true-match or known non-match).
    This function is used to calculate both the m- and u-probabilities,
    depending on the pair sample it is given.

    :param true_match_pairs: A sequence of tuples containing pairs 
      of patient data dictionaries.
    :returns: A dictionary mapping Feature names to their class
      probabilities.
    """
    # LaPlacian smoothing accounts for unseen instances
    class_probs = {str(f): 1.0 for f in FIELDS_TO_CALCULATE}

    for pair in sampled_pairs:
        pii_record_1 = PIIRecord.from_data(pair[0])
        pii_record_2 = PIIRecord.from_data(pair[1])

        # The probabilistic exact matcher nicely uses feature_iter and
        # cross-value checking for us; if we award 0 points for missing
        # data and 1 point for perfect agreement, we get the count
        for f in FIELDS_TO_CALCULATE:
            comparison = compare_probabilistic_exact_match(
                pii_record_1, pii_record_2, f, 1.0, 0.0, prepend_suffix=False
            )
            class_probs[str(f)] += comparison[0]
    
    for k in class_probs:
        class_probs[k] /= float(len(sampled_pairs) + 1)
    
    return class_probs


def calculate_log_odds(
        m_probs: dict[str, float],
        u_probs: dict[str, float]
    ) -> dict[str, float]:
    """
    Given class-conditional probabilities for field agreement, calculate
    the log-odds values for each field of calculable interest for
    patient matching.

    :param m_probs: The class-conditional likelihood of fields agreeing,
      given two records are a match.
    :param u_probs: The class-conditional likelihood of fields agreeing,
      given two records are not a match.
    :returns: A dictionary mapping Feature names to their log-odds values.
    """
    log_odds = {}
    for field in m_probs:
        log_odds[field] = math.log(m_probs[field] / u_probs[field])
    return log_odds
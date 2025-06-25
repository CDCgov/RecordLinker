import math
import typing

from recordlinker.linking.matchers import compare_probabilistic_exact_match
from recordlinker.linking.skip_values import remove_skip_values
from recordlinker.schemas import algorithm as ag
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

    :param sampled_pairs: A sequence of tuples containing pairs 
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


def calculate_and_sort_tuning_scores(
    true_match_pairs: typing.Sequence[typing.Tuple[dict, dict]],
    non_match_pairs: typing.Sequence[typing.Tuple[dict, dict]],
    log_odds: dict[str, float],
    algorithm: ag.Algorithm
) -> typing.Tuple[list[float], list[float]]:
    """
    Given a set of true-matching pairs and a set of non-matching pairs
    obtained from database sampling, calculates the pairwise RMS for
    each collection and sorts the resulting scores. The evaluation
    steps of the given algorithm are invoked on each pair of each class,
    using the provided log-odds to compute RMS. Used for estimating
    RMS possible match window boundaries and graphing distributions.

    :param true_match_pairs: A sequence of tuples containing known
      matching pairs of patient data dictionaries.
    :param non_match_pairs: A sequence of tuples containing known non-
      matching pairs of patient data dictionaries.
    :param log_odds: A dictionary mapping Feature string names to their
      computed log-odds values.
    :param algorithm: A schema defining an algorithm to use for estimating
      RMS threshold boundaries.
    :returns: A tuple containing sorted lists of class RMS scores..
    """
    context: ag.AlgorithmContext = algorithm.algorithm_context

    # Calculate the maximum number of log odds points for each pass at the top
    # so we don't waste computations in the main loop below
    max_points: dict[str, float] = {}
    for idx, algorithm_pass in enumerate(algorithm.passes):
        max_points_in_pass: float = sum(
            [log_odds[str(e.feature)] or 0.0 for e in algorithm_pass.evaluators]
        )
        max_points[algorithm_pass.label or f"pass_{idx}"] = max_points_in_pass

    true_match_scores: list[float] = _score_pairs_in_class(
        true_match_pairs, log_odds, max_points, algorithm, context
    )
    non_match_scores: list[float] = _score_pairs_in_class(
        non_match_pairs, log_odds, max_points, algorithm, context
    )
    true_match_scores = sorted(true_match_scores)
    non_match_scores = sorted(non_match_scores)
    return (true_match_scores, non_match_scores)


def estimate_rms_bounds(
    true_match_scores: list[float],
    non_match_scores: list[float],
) -> typing.Tuple[float, float]:
    """
    Identifies suggested boundaries for the RMS possible match window
    using previously sampled pairs of true and non matches. 

    :param true_match_pairs: A sequence of tuples containing known
      matching pairs of patient data dictionaries.
    :param non_match_pairs: A sequence of tuples containing known non-
      matching pairs of patient data dictionaries.
    :returns: A tuple containing the Minimum Match Threshold and the Certain
      Match Threshold suggested by the input data.
    """
    # Overlap the lists to find the possible match window:
    # MMT is first non-match score greater than smallest true-match score
    # CMT is first true-match score greater than all non-match scores
    mmt = None
    cmt = None
    for t in non_match_scores:
        if t >= true_match_scores[0]:
            mmt = t
            break
    for t in true_match_scores:
        if t > non_match_scores[-1]:
            cmt = t
            break

    # To account for unseen data, buffer each threshold by pushing it 
    # towards its respective distribution's extreme
    if mmt is not None:
        mmt = max([0, mmt - 0.025])
    if cmt is not None:
        cmt = min([1.0, cmt + 0.025])
    
    # Edge Case 1: Distributions are totally disjoint
    # MMT can just be set to the highest non-match score
    if mmt is None:
        mmt = non_match_scores[-1]

    # Edge Case 2: No true match score larger than largest non-match
    # This is EXTREMELY unnatural and can only happen if either the
    # distributions are inverted (true match scores left of non-match
    # scores) or the true-match curve is a subset contained entirely 
    # within the non-match curve--in either case, the problem is likely
    # the data and not the scoring procedure
    if cmt is None:
        # Best we can do is set the CMT to be beyond the range of the
        # non-match curve
        cmt = min([non_match_scores[-1] + 0.01, 1.0])
    
    return (mmt, cmt)


def _compare_records_in_pair(
    record_1: PIIRecord,
    record_2: PIIRecord,
    log_odds: dict[str, float],
    max_log_odds_points: float,
    algorithm_pass: ag.AlgorithmPass,
    context: ag.AlgorithmContext,
) -> float:
    """
    Helper function to perform a feature-wise comparison against two records
    in a tuning pair. This function is similar to the `compare` function used
    in linking.py, except that log_odds weights and the log_odds_maximum are
    manually provided, and feature-wise individual contributions are not
    tracked separately.

    :param record_1: The first patient record in a pair.
    :param record_2: The second patient record in a pair.
    :param log_odds: A dictionary mapping Feature string names to their
      calculated log-odds values.
    :param max_log_odds_points: The maximum number of log-odds points that can
      be scored in the pass of the algorithm in which the records are being
      compared.
    :param algorithm_pass: The schema for the algorithm pass in which the 
      records are being compared.
    :param context: The schema for the algorithm context being used.
    :returns: The number of log-odds points earned by the comparison between
      the two records.
    """
    missing_field_weights: float = 0.0
    results: list[float] = []
    max_missing_proportion: float = context.advanced.max_missing_allowed_proportion
    for evaluator in algorithm_pass.evaluators:
        log_odds_for_field: float = log_odds[str(evaluator.feature)] or 0.0
        # Evaluate the comparison function, track missingness, and append the
        # score component to the list
        fn: typing.Callable = evaluator.func.callable()
        kwargs = {
            "log_odds": log_odds_for_field,
            "missing_field_points_proportion": context.advanced.missing_field_points_proportion,
            "fuzzy_match_threshold": evaluator.fuzzy_match_threshold
            or context.advanced.fuzzy_match_threshold,
            "fuzzy_match_measure": evaluator.fuzzy_match_measure
            or context.advanced.fuzzy_match_measure,
        }
        result: tuple[float, bool] = fn(record_1, record_2, evaluator.feature, **kwargs)
        if result[1]:
            # The field was missing, so update the running tally of how much
            # the candidate is missing overall
            missing_field_weights += log_odds_for_field
        results.append(result[0])

    # Make sure this score wasn't just accumulated with missing checks
    if missing_field_weights <= (max_missing_proportion * max_log_odds_points):
        rule_result = sum(results)
    else:
        rule_result = 0.0
    return rule_result


def _score_pairs_in_class(
        class_sample: typing.Sequence[typing.Tuple[dict, dict]],
        log_odds: dict[str, float],
        max_points: dict[str, float],
        algorithm: ag.Algorithm,
        context: ag.AlgorithmContext,
    ) -> list[float]:
    """
    Given a sample of class-partitioned data and a record linkage algorithm,
    compute the RMS of each pair in the class sample, taking the best RMS
    the pair could have scored across all passes of the provided algorithm.

    :param class_sample: A sequence of tuples of pairs of patient data
      dictionaries, each belonging to the same class of tuning data (either
      known true-match or known non-match).
    :param log_odds: A dictionary mapping Feature string names to their 
      calculated log-odds values.
    :param max_points: A dictionary mapping the name of each pass of an 
      algorithm to the maximum possible number of log-odds points obtainable
      in that pass.
    :param algorithm: The schema for an algorithm to use for comparing the
      record pairs.
    :param context: The schema for an algorithm context to use.
    :returns: A list of RMS values, one for each input pair.
    """
    class_scores: list[float] = []
    for pair in class_sample:
        pii_record_1 = PIIRecord.from_data(pair[0])
        pii_record_1 = remove_skip_values(pii_record_1, context.skip_values)
        pii_record_2 = PIIRecord.from_data(pair[1])
        pii_record_2 = remove_skip_values(pii_record_2, context.skip_values)

        # We need to find the best RMS across all passes that this pair
        # could achieve
        scores_across_passes = []
        for idx, algorithm_pass in enumerate(algorithm.passes):
            max_points_in_pass = max_points[algorithm_pass.label or f"pass_{idx}"]
            score_in_pass = _compare_records_in_pair(
                pii_record_1,
                pii_record_2,
                log_odds,
                max_points_in_pass,
                algorithm_pass,
                context
            )
            scores_across_passes.append(score_in_pass / max_points_in_pass)
        class_scores.append(max(scores_across_passes))
    return class_scores
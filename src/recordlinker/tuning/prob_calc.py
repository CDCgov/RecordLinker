import math
import typing

from recordlinker.linking.matchers import compare_probabilistic_exact_match
from recordlinker.linking.skip_values import remove_skip_values
from recordlinker.schemas import algorithm as ag
from recordlinker.schemas.pii import Feature
from recordlinker.schemas.pii import FeatureAttribute
from recordlinker.schemas.pii import PIIRecord
from recordlinker.schemas.tuning import TuningPair
from recordlinker.schemas.tuning import TuningProbabilities

# We don't need log-odds for every Feature we register, since some
# are folded into other evaluations
FIELDS_TO_IGNORE = ["GIVEN_NAME", "NAME", "SUFFIX"]
FIELDS_TO_CALCULATE = [
    Feature.parse(f.value) for f in FeatureAttribute if f.value not in FIELDS_TO_IGNORE
]


def calculate_class_probs(sampled_pairs: typing.Iterable[TuningPair]) -> TuningProbabilities:
    """
    Calculate the class-conditional likelihood that two records will
    agree on a particular field, given that the two records are a
    belong to the same class (known true-match or known non-match).
    This function is used to calculate both the m- and u-probabilities,
    depending on the pair sample it is given.

    :param sampled_pairs: An iterable of TuningPairs
    :returns: A TuningProbabilities object
    """
    # LaPlacian smoothing accounts for unseen instances
    result: TuningProbabilities = TuningProbabilities(
        probs={f: 1.0 for f in FIELDS_TO_CALCULATE}, count=0
    )

    for pair in sampled_pairs:
        # The probabilistic exact matcher nicely uses feature_iter and
        # cross-value checking for us; if we award 0 points for missing
        # data and 1 point for perfect agreement, we get the count
        result.count += 1
        result.sample_used = pair.sample_used
        for f in FIELDS_TO_CALCULATE:
            comparison, _ = compare_probabilistic_exact_match(
                pair.record1, pair.record2, f, 1.0, 0.0, prepend_suffix=False
            )
            result.probs[f] += comparison

    for f in result.probs:
        result.probs[f] /= float(result.count + 1)

    return result


def calculate_log_odds(
    m_probs: dict[Feature, float], u_probs: dict[Feature, float]
) -> dict[Feature, float]:
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
    log_odds: dict[Feature, float] = {}
    for field in m_probs:
        log_odds[field] = math.log(m_probs[field] / u_probs[field])
    return log_odds


def calculate_and_sort_tuning_scores(
    true_match_pairs: typing.Iterable[TuningPair],
    non_match_pairs: typing.Iterable[TuningPair],
    log_odds: dict[Feature, float],
    algorithm: ag.Algorithm,
) -> dict[str, typing.Tuple[list[float], list[float]]]:
    """
    Given a set of true-matching pairs and a set of non-matching pairs
    obtained from database sampling, calculates the pairwise RMS for
    each collection, for each pass of the algorithm, and sorts the
    resulting scores. The evaluation steps of the given algorithm are
    invoked on each pair of each class, using the provided log-odds
    to compute RMS.

    :param true_match_pairs: An iterable of TuningPairs containing known
      matching pairs of patient data dictionaries.
    :param non_match_pairs: An iterable of TuningPairs containing known non-
      matching pairs of patient data dictionaries.
    :param log_odds: A dictionary mapping Feature string names to their
      computed log-odds values.
    :param algorithm: A schema defining an algorithm to use for estimating
      RMS threshold boundaries.
    :returns: A dictonary mapping the names of the algorithm's passes to
      a tuple containing sorted lists of class RMS scores.
    """
    sorted_scores: dict[str, typing.Tuple[list[float], list[float]]] = {
        p.resolved_label: ([], []) for p in algorithm.passes
    }
    max_points: dict[str, float] = {
        p.resolved_label: sum([log_odds.get(e.feature, 0.0) for e in p.evaluators])
        for p in algorithm.passes
    }

    # Both true-match and non-match pairs are iterables and can only be accessed once,
    # we need to use the pairs to calculate values for all passes in the Algorithm, thus we
    # need to iterate over the pairs first, then the passes
    for pair in true_match_pairs:
        for key, score in _score_records_in_pair(pair, log_odds, max_points, algorithm).items():
            sorted_scores[key][0].append(score)
    for pair in non_match_pairs:
        for key, score in _score_records_in_pair(pair, log_odds, max_points, algorithm).items():
            sorted_scores[key][1].append(score)

    for key in sorted_scores:
        sorted_scores[key][0].sort()
        sorted_scores[key][1].sort()

    return sorted_scores


def estimate_rms_bounds(
    sorted_scores: dict[str, typing.Tuple[list[float], list[float]]],
) -> dict[str, typing.Tuple[float, float]]:
    """
    Identifies suggested boundaries for the RMS possible match windows
    of each pass of an algorithm, using previously sampled pairs of
    true and non matches.

    :param sorted_scores: A dictionary mapping the names of the passes of
      a linkage algorithm to a tuple containing class-partitioned lists
      of pairwise RMS values.
    :returns: A dictionary mapping the names of the passes of an algorithm
      to a tuple containing the Minimum Match Threshold and the Certain
      Match Threshold suggested by the input data.
    """
    suggested_bounds = {}

    for k in sorted_scores:
        # Don't count any vacuous 0s in the true match class towards the boundary
        # of minimum thresholding--we want the MMT to apply to the real bulk of
        # the distribution farther down the axis
        true_match_scores = [x for x in sorted_scores[k][0] if x > 0.0]
        non_match_scores = sorted_scores[k][1]

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

        suggested_bounds[k] = (mmt, cmt)
    return suggested_bounds


def _compare_records_in_pair(
    record_1: PIIRecord,
    record_2: PIIRecord,
    log_odds: dict[Feature, float],
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
        log_odds_for_field: float = log_odds.get(evaluator.feature, 0.0)
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


def _score_records_in_pair(
    pair: TuningPair,
    log_odds: dict[Feature, float],
    max_points: dict[str, float],
    algorithm: ag.Algorithm,
) -> dict[str, float]:
    """
    Given a TuningPair and an Algorithm, calculate the RMS for each pass.

    :param pair: A TuningPair containing two patient records.
    :param log_odds: A dictionary mapping Feature string names to their
      calculated log-odds values.
    :param max_points: A dictionary mapping the names of the algorithm's
      passes to the maximum number of log-odds points that can be scored in
      the pass.
    :param algorithm: A schema defining an algorithm to use for estimating
      RMS threshold boundaries.
    :returns: A dictionary mapping the names of the algorithm's passes to
    """
    result: dict[str, float] = {}
    ctx: ag.AlgorithmContext = algorithm.algorithm_context
    rec1: PIIRecord = remove_skip_values(pair.record1, ctx.skip_values)
    rec2: PIIRecord = remove_skip_values(pair.record2, ctx.skip_values)
    for _pass in algorithm.passes:
        key: str = _pass.resolved_label
        val: float = _compare_records_in_pair(rec1, rec2, log_odds, max_points[key], _pass, ctx)
        result[key] = val / max_points[key] if max_points[key] else 0.0
    return result

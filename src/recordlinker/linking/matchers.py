"""
recordlinker.linking.matchers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains functions for evaluating whether two records are
a match based on the similarity of their features. These functions are
used by the record linkage algorithm to determine whether a candidate
pair of records should be considered a match or not.
"""

import enum
import typing

import rapidfuzz

from recordlinker.models.mpi import Patient
from recordlinker.schemas.pii import Feature
from recordlinker.schemas.pii import PIIRecord

SIMILARITY_MEASURES = typing.Literal["JaroWinkler", "Levenshtein", "DamerauLevenshtein"]


class RuleFunc(enum.Enum):
    """
    Enum for the different types of match rules that can be used for patient
    matching. This is the universe of all possible match rules that a user can
    choose from when configuring their algorithm.  When data is loaded into the
    MPI, all possible RuleFuncs will be created for the defined match rules.
    However, only a subset will be used in matching, based on the configuration of
    the algorithm.
    """

    RULE_PROBABILISTIC_MATCH = "func:recordlinker.linking.matchers.rule_probabilistic_match"


class FeatureFunc(enum.Enum):
    """
    Enum for the different types of feature comparison functions that can be used
    for patient matching. This is the universe of all possible feature comparison
    functions that a user can choose from when configuring their algorithm.  When
    data is loaded into the MPI, all possible FeatureFuncs will be created for the
    defined feature comparison functions. However, only a subset will be used in
    matching, based on the configuration of the algorithm.
    """

    COMPARE_PROBABILISTIC_EXACT_MATCH = (
        "func:recordlinker.linking.matchers.compare_probabilistic_exact_match"
    )
    COMPARE_PROBABILISTIC_FUZZY_MATCH = (
        "func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match"
    )


# TODO: DELETE
class AvailableKwarg(enum.Enum):
    """
    Enum for the different types of keyword arguments that can be used in the
    AlgorithmPass schema. This is the universe of all possible keyword arguments
    that a user can choose from when configuring their algorithm.  When data is
    loaded into the MPI, all possible AvailableKwargs will be created for the
    defined keyword arguments. However, only a subset will be used in matching,
    based on the configuration of the algorithm.
    """

    SIMILARITY_MEASURE = "similarity_measure"
    THRESHOLD = "threshold"
    THRESHOLDS = "thresholds"
    LOG_ODDS = "log_odds"
    TRUE_MATCH_THRESHOLD = "true_match_threshold"


def rule_probabilistic_match(feature_comparisons: list[float], threshold: float) -> bool:
    """
    Determines whether a given set of feature comparisons matches enough
    to be the result of a true patient link instead of just random chance.
    This is represented using previously computed log-odds ratios.

    :param feature_comparisons: A list of floats representing the log-odds
      score of each field computed on.
    :param threshold: The minimum score required to classify a match.
    :return: Whether the feature comparisons score well enough to be
      considered a match.
    """
    return sum(feature_comparisons) >= threshold


def compare_probabilistic_exact_match(
    record: PIIRecord, patient: Patient, key: Feature, log_odds: float, **kwargs: typing.Any
) -> float:
    """
    Compare the same Feature Field in two patient records, one incoming and one
    previously seen, to determine whether the fields fully agree.
    If they do, the full log-odds weight-points for this field are added to the
    record pair's match strength. Otherwise, no points are added.

    :param record: The incoming record to evaluate.
    :param patient: The patient record to compare against.
    :param key: The name of the column being evaluated (e.g. "city").
    :param log_odds: The log-odds weight-points for this field
    :param **kwargs: Optionally, a dictionary including specifications for
      the string comparison metric to use, as well as the cutoff score
      beyond which to classify the strings as a partial match.
    :return: A float of the score the feature comparison earned.
    """
    agree = 0.0
    for x in patient.record.feature_iter(key):
        for y in record.feature_iter(key):
            # for each permutation of values, check whether the values agree
            if x == y:
                agree = 1.0
                break
    return agree * log_odds


def compare_probabilistic_fuzzy_match(
    record: PIIRecord, patient: Patient, key: Feature, log_odds: float, **kwargs: typing.Any
) -> float:
    """
    Compare the same Feature Field in two patient records, one incoming and one
    previously seen, to determine the extent to which the fields agree.
    If their string similarity score (agreement) is above a minimum threshold
    specified as a kwarg, that proportion of the Field's maximum log-odds
    weight points are added to the record match strength. Otherwise, no points
    are added.

    :param record: The incoming record to evaluate.
    :param patient: The patient record to compare against.
    :param key: The name of the column being evaluated (e.g. "city").
    :param log_odds: The log-odds weight-points for this field
    :param **kwargs: Optionally, a dictionary including specifications for
      the string comparison metric to use, as well as the cutoff score
      beyond which to classify the strings as a partial match.
    :return: A float of the score the feature comparison earned.
    """
    measure = kwargs.get("fuzzy_match_measure")
    threshold = kwargs.get("fuzzy_match_threshold")
    assert measure in typing.get_args(SIMILARITY_MEASURES), "fuzzy match measure must be specified"
    comp_func = getattr(rapidfuzz.distance, str(measure)).normalized_similarity
    assert isinstance(threshold, float), "fuzzy match threshold must be specified"
    threshold = float(threshold)

    max_score = 0.0
    for x in patient.record.feature_iter(key):
        for y in record.feature_iter(key):
            # for each permutation of values, find the score and record it if its
            # larger than any previous score
            max_score = max(comp_func(x, y), max_score)
    if max_score < threshold:
        # return 0 if our max score is less than the threshold
        return 0.0
    return max_score * log_odds

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


def _get_fuzzy_params(col: str, **kwargs) -> tuple[SIMILARITY_MEASURES, float]:
    """
    Helper method to quickly determine the appropriate similarity measure
    and fuzzy matching threshold to use for fuzzy-comparing a particular
    field between two records.

    :param col: The string name of the column being used in a fuzzy
      comparison.
    :param kwargs: Optionally, a dictionary of keyword arguments containing
      values for a similarity metric and appropriate fuzzy thresholds.
    :return: A tuple containing the similarity metric to use and the
      fuzzy comparison threshold to measure against.
    """
    similarity_measure: SIMILARITY_MEASURES = "JaroWinkler"
    if "similarity_measure" in kwargs:
        similarity_measure = kwargs["similarity_measure"]
        # Ensure the similarity measure is valid
        if similarity_measure not in typing.get_args(SIMILARITY_MEASURES):
            raise ValueError(f"Invalid similarity measure: {similarity_measure}")

    threshold: float = 0.7
    if "thresholds" in kwargs:
        if col in kwargs["thresholds"]:
            threshold = kwargs["thresholds"][col]
    elif "threshold" in kwargs:
        threshold = kwargs["threshold"]

    return (similarity_measure, threshold)


def rule_probabilistic_match(feature_comparisons: list[float], **kwargs: typing.Any) -> bool:
    """
    Determines whether a given set of feature comparisons matches enough
    to be the result of a true patient link instead of just random chance.
    This is represented using previously computed log-odds ratios.

    :param feature_comparisons: A list of floats representing the log-odds
      score of each field computed on.
    :return: Whether the feature comparisons score well enough to be
      considered a match.
    """
    threshold: typing.Any = kwargs.get("true_match_threshold")
    if threshold is None:
        raise KeyError("Cutoff threshold for true matches must be passed.")
    return sum(feature_comparisons) >= float(threshold)


def compare_probabilistic_exact_match(
    record: PIIRecord,
    patient: Patient,
    key: Feature,
    missing_field_points_proportion: float,
    **kwargs: typing.Any
) -> tuple[float, bool]:
    """
    Compare the same Feature Field in two patient records, one incoming and one
    previously seen, to determine whether the fields fully agree.
    If they do, the full log-odds weight-points for this field are added to the
    record pair's match strength. Otherwise, no points are added.
    If one or both of the Fields are missing (including blank or unknown), a
    proportion of log-odds points specified in the algorithm configuration is
    awarded.
    In all cases, the comparison function captures whether one or both records
    had missing information.

    :param record: The incoming record to evaluate.
    :param patient: The patient record to compare against.
    :param key: The name of the column being evaluated (e.g. "city").
    :param missing_field_points_proportion: The proportion of log-odds points to
      award if one of the records is missing information in the given field.
    :param **kwargs: Optionally, a dictionary including specifications for
      the string comparison metric to use, as well as the cutoff score
      beyond which to classify the strings as a partial match.
    :return: A tuple containing: a float of the score the feature comparison
      earned, and a boolean indicating whether one of the Fields was missing.
    """
    log_odds = kwargs.get("log_odds", {}).get(str(key.attribute))
    if log_odds is None:
        raise ValueError(f"Log odds not found for feature {key}")

    # Return early if a field is missing, and log that was the case
    incoming_record_fields = list(patient.record.feature_iter(key))
    mpi_record_fields = list(record.feature_iter(key))
    if len(incoming_record_fields) == 0 or len(mpi_record_fields) == 0:
        return (missing_field_points_proportion * log_odds, True)

    agree = 0.0
    for x in incoming_record_fields:
        for y in mpi_record_fields:
            # for each permutation of values, check whether the values agree
            if (x == y):
                agree = 1.0
                break
    return (agree * log_odds, False)


def compare_probabilistic_fuzzy_match(
    record: PIIRecord,
    patient: Patient,
    key: Feature,
    missing_field_points_proportion: float,
    **kwargs: typing.Any
) -> tuple[float, bool]:
    """
    Compare the same Feature Field in two patient records, one incoming and one
    previously seen, to determine the extent to which the fields agree.
    If their string similarity score (agreement) is above a minimum threshold
    specified as a kwarg, that proportion of the Field's maximum log-odds
    weight points are added to the record match strength. Otherwise, no points
    are added.
    If one or both of the Fields are missing (including blank or unknown), a
    proportion of log-odds points specified in the algorithm configuration is
    awarded.
    In all cases, the comparison function captures whether one or both records
    had missing information.

    :param record: The incoming record to evaluate.
    :param patient: The patient record to compare against.
    :param key: The name of the column being evaluated (e.g. "city").
    :param missing_field_points_proportion: The proportion of log-odds points
      to award if one of the records is missing information in the given field.
    :param **kwargs: Optionally, a dictionary including specifications for
      the string comparison metric to use, as well as the cutoff score
      beyond which to classify the strings as a partial match.
    :return: A tuple containing: a float of the score the feature comparison
      earned, and a boolean indicating whether one of the Fields was missing.
    """
    log_odds = kwargs.get("log_odds", {}).get(str(key.attribute))
    if log_odds is None:
        raise ValueError(f"Log odds not found for feature {key}")
    
    # Return early if a field is missing, and log that was the case
    incoming_record_fields = list(patient.record.feature_iter(key))
    mpi_record_fields = list(record.feature_iter(key))
    if len(incoming_record_fields) == 0 or len(mpi_record_fields) == 0:
        return (missing_field_points_proportion * log_odds, True)

    similarity_measure, threshold = _get_fuzzy_params(str(key.attribute), **kwargs)
    comp_func = getattr(rapidfuzz.distance, similarity_measure).normalized_similarity
    max_score = 0.0
    for x in incoming_record_fields:
        for y in mpi_record_fields:
            # for each permutation of values, find the score and record it if its
            # larger than any previous score
            max_score = max(comp_func(x, y), max_score)
    if max_score < threshold:
        # return 0 if our max score is less than the threshold
        return (0.0, False)
    return (max_score * log_odds, False)

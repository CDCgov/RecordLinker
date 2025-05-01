"""
recordlinker.linking.matchers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains functions for evaluating whether two records are
a match based on the similarity of their features. These functions are
used by the record linkage algorithm to determine whether a candidate
pair of records should be considered a match or not.
"""

import enum
import sys
import typing

import rapidfuzz

from recordlinker.schemas.pii import Feature
from recordlinker.schemas.pii import PIIRecord

SIMILARITY_MEASURES = typing.Literal["JaroWinkler", "Levenshtein", "DamerauLevenshtein"]


class FeatureFunc(enum.Enum):
    """
    Enum for the different types of feature comparison functions that can be used
    for patient matching. We recommend using COMPARE_PROBABILISTIC_EXACT_MATCH for
    features that are comparing to a set of known values (e.g. "SEX", "RACE").  For
    all other features, we recommend using COMPARE_PROBABILISTIC_FUZZY_MATCH.
    """

    COMPARE_PROBABILISTIC_EXACT_MATCH = "COMPARE_PROBABILISTIC_EXACT_MATCH"
    COMPARE_PROBABILISTIC_FUZZY_MATCH = "COMPARE_PROBABILISTIC_FUZZY_MATCH"

    def __str__(self) -> str:
        """
        Returns the string representation of the FeatureFunc.
        """
        return self.value

    def callable(self) -> typing.Callable:
        """
        Returns the callable associated with the FeatureFunc.
        """
        if not hasattr(self, "_callable"):
            self._callable = getattr(sys.modules[__name__], self.value.lower())
        return self._callable


def compare_probabilistic_exact_match(
    record: PIIRecord,
    mpi_record: PIIRecord,
    key: Feature,
    log_odds: float,
    missing_field_points_proportion: float,
    **kwargs: typing.Any,
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
    :param mpi_record: The MPI record to compare against.
    :param key: The name of the column being evaluated (e.g. "city").
    :param log_odds: The log-odds weight-points for this field
    :param missing_field_points_proportion: The proportion of log-odds points to
      award if one of the records is missing information in the given field.
    :param **kwargs: Optionally, a dictionary including specifications for
      the string comparison metric to use, as well as the cutoff score
      beyond which to classify the strings as a partial match.
    :return: A tuple containing: a float of the score the feature comparison
      earned, and a boolean indicating whether one of the Fields was missing.
    """
    incoming_record_fields = list(record.feature_iter(key))
    mpi_record_fields = list(mpi_record.feature_iter(key))
    if len(incoming_record_fields) == 0 or len(mpi_record_fields) == 0:
        # Return early if a field is missing, and log that was the case
        return (missing_field_points_proportion * log_odds, True)

    agree = 0.0
    for x in incoming_record_fields:
        for y in mpi_record_fields:
            # for each permutation of values, check whether the values agree
            if x == y:
                agree = 1.0
                break
    return (agree * log_odds, False)


def compare_probabilistic_fuzzy_match(
    record: PIIRecord,
    mpi_record: PIIRecord,
    key: Feature,
    log_odds: float,
    missing_field_points_proportion: float,
    **kwargs: typing.Any,
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
    :param mpi_record: The MPI record to compare against.
    :param key: The name of the column being evaluated (e.g. "city").
    :param log_odds: The log-odds weight-points for this field
    :param missing_field_points_proportion: The proportion of log-odds points
      to award if one of the records is missing information in the given field.
    :param **kwargs: Optionally, a dictionary including specifications for
      the string comparison metric to use, as well as the cutoff score
      beyond which to classify the strings as a partial match.
    :return: A tuple containing: a float of the score the feature comparison
      earned, and a boolean indicating whether one of the Fields was missing.
    """
    fuzzy_match_measure: typing.Any  = kwargs.get("fuzzy_match_measure", None)
    fuzzy_match_threshold: typing.Any = kwargs.get("fuzzy_match_threshold", None)
    assert fuzzy_match_measure in typing.get_args(SIMILARITY_MEASURES), f"Invalid similarity measure: {fuzzy_match_measure}"
    assert isinstance(fuzzy_match_threshold, float), f"Invalid similarity threshold: {fuzzy_match_threshold}"
    measure: SIMILARITY_MEASURES = fuzzy_match_measure
    threshold: float = float(fuzzy_match_threshold)

    incoming_record_fields = list(record.feature_iter(key))
    mpi_record_fields = list(mpi_record.feature_iter(key))
    if len(incoming_record_fields) == 0 or len(mpi_record_fields) == 0:
        # Return early if a field is missing, and log that was the case
        return (missing_field_points_proportion * log_odds, True)

    comp_func = getattr(rapidfuzz.distance, measure).normalized_similarity
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

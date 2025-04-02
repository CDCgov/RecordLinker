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

from recordlinker.models.mpi import Patient
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
    patient: Patient,
    key: Feature,
    log_odds: float,
    missing_proportion: float,
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
    :param patient: The patient record to compare against.
    :param key: The name of the column being evaluated (e.g. "city").
    :param log_odds: The log-odds weight-points for this field
    :param missing_proportion: The proportion of log-odds points to
      award if one of the records is missing information in the given field.
    :return: A tuple containing: a float of the score the feature comparison
      earned, and a boolean indicating whether one of the Fields was missing values.
    """
    incoming_record_fields = list(patient.record.feature_iter(key))
    mpi_record_fields = list(record.feature_iter(key))
    if len(incoming_record_fields) == 0 or len(mpi_record_fields) == 0:
        # return early if a field is missing
        return (log_odds * missing_proportion, True)

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
    patient: Patient,
    key: Feature,
    log_odds: float,
    missing_proportion: float,
    fuzzy_match_measure: SIMILARITY_MEASURES,
    fuzzy_match_threshold: float,
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
    :param patient: The patient record to compare against.
    :param key: The name of the column being evaluated (e.g. "city").
    :param log_odds: The log-odds weight-points for this field
    :param missing_proportion: The proportion of log-odds points to
      award if one of the records is missing information in the given field.
    :param fuzzy_match_measure: The string comparison metric to use
    :params fuzzy_match_threshold: The cutoff score beyond which to classify the strings as a partial match
    :return: A tuple containing: a float of the score the feature comparison
      earned, and a boolean indicating whether one of the Fields was missing values.
    """
    incoming_record_fields = list(patient.record.feature_iter(key))
    mpi_record_fields = list(record.feature_iter(key))
    if len(incoming_record_fields) == 0 or len(mpi_record_fields) == 0:
        # return early if a field is missing
        return (log_odds * missing_proportion, True)

    cmp_fn = getattr(rapidfuzz.distance, str(fuzzy_match_measure)).normalized_similarity
    max_score = 0.0
    for x in incoming_record_fields:
        for y in mpi_record_fields:
            # for each permutation of values, find the score and record it if its
            # larger than any previous score
            max_score = max(cmp_fn(x, y), max_score)
    if max_score < fuzzy_match_threshold:
        # return 0 if our max score is less than the threshold
        return (0.0, False)
        # return early if a field is missing
    return (max_score * log_odds, False)

"""
recordlinker.linkage.matchers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains functions for evaluating whether two records are
a match based on the similarity of their features. These functions are
used by the record linkage algorithm to determine whether a candidate
pair of records should be considered a match or not.
"""
import typing

import rapidfuzz

from recordlinker.linkage import utils

SIMILARITY_MEASURES = typing.Literal["JaroWinkler", "Levenshtein", "DamerauLevenshtein"]


def compare_strings(
    string1: str,
    string2: str,
    similarity_measure: SIMILARITY_MEASURES = "JaroWinkler",
) -> float:
    """
    Returns the normalized similarity measure between string1 and string2, as
    determined by the similarlity measure. The higher the normalized similarity measure
    (up to 1.0), the more similar string1 and string2 are. A normalized similarity
    measure of 0.0 means string1 and string 2 are not at all similar. This function
    expects basic text cleaning (e.g. removal of numeric characters, trimming of spaces,
    etc.) to already have been performed on the input strings.

    :param string1: First string for comparison.
    :param string2: Second string for comparison.
    :param similarity_measure: The method used to measure the similarity between two
        strings, defaults to "JaroWinkler".
     - JaroWinkler: a ratio of matching characters and transpositions needed to
        transform string1 into string2.
     - Levenshtein: the number of edits (excluding transpositions) needed to transform
        string1 into string2.
     - DamerauLevenshtein: the number of edits (including transpositions) needed to
        transform string1 into string2.
    :return: The normalized similarity between string1 and string2, with 0 representing
        no similarity between string1 and string2, and 1 meaning string1 and string2 are
        dentical words.
    """
    if similarity_measure == "JaroWinkler":
        return rapidfuzz.distance.JaroWinkler.normalized_similarity(string1, string2)
    elif similarity_measure == "Levenshtein":
        return rapidfuzz.distance.Levenshtein.normalized_similarity(string1, string2)
    elif similarity_measure == "DamerauLevenshtein":
        return rapidfuzz.distance.DamerauLevenshtein.normalized_similarity(
            string1, string2
        )


def eval_perfect_match(feature_comparisons: list, **kwargs) -> bool:
    """
    Determines whether a given set of feature comparisons represent a
    'perfect' match (i.e. whether all features that were compared match
    in whatever criteria was specified for them).

    :param feature_comparisons: A list of 1s and 0s, one for each feature
      that was compared during the match algorithm.
    :return: The evaluation of whether the given features all match.
    """
    return sum(feature_comparisons) == len(feature_comparisons)


def eval_log_odds_cutoff(feature_comparisons: list, **kwargs) -> bool:
    """
    Determines whether a given set of feature comparisons matches enough
    to be the result of a true patient link instead of just random chance.
    This is represented using previously computed log-odds ratios.

    :param feature_comparisons: A list of floats representing the log-odds
      score of each field computed on.
    :return: Whether the feature comparisons score well enough to be
      considered a match.
    """
    if "true_match_threshold" not in kwargs:
        raise KeyError("Cutoff threshold for true matches must be passed.")
    return sum(feature_comparisons) >= kwargs["true_match_threshold"]


def feature_match_exact(
    record_i: list,
    record_j: list,
    feature_col: str,
    col_to_idx: dict[str, int],
    **kwargs: dict,
) -> bool:
    """
    Determines whether a single feature in a given pair of records
    constitutes an exact match (perfect equality).

    :param record_i: One of the records in the candidate pair to evaluate.
    :param record_j: The second record in the candidate pair.
    :param feature_col: The name of the column being evaluated (e.g. "city").
    :param col_to_idx: A dictionary mapping column names to the numeric index
      in which they occur in order in the data.
    :return: A boolean indicating whether the features are an exact match.
    """
    idx = col_to_idx[feature_col]
    return record_i[idx] == record_j[idx]


def feature_match_four_char(
    record_i: list,
    record_j: list,
    feature_col: str,
    col_to_idx: dict[str, int],
    **kwargs: dict,
) -> bool:
    """
    Determines whether a string feature in a pair of records exactly matches
    on the first four characters.

    :param record_i: One of the records in the candidate pair to evaluate.
    :param record_j: The second record in the candidate pair.
    :param feature_col: The name of the column being evaluated (e.g. "city").
    :param col_to_idx: A dictionary mapping column names to the numeric index
      in which they occur in order in the data.
    :return: A boolean indicating whether the features are a match.
    """
    idx = col_to_idx[feature_col]
    first_four_i = record_i[idx][: min(4, len(record_i[idx]))]
    first_four_j = record_j[idx][: min(4, len(record_j[idx]))]
    return first_four_i == first_four_j


def feature_match_fuzzy_string(
    record_i: list,
    record_j: list,
    feature_col: str,
    col_to_idx: dict[str, int],
    **kwargs: dict,
) -> bool:
    """
    Determines whether two strings in a given pair of records are close
    enough to constitute a partial match. The exact nature of the match
    is determined by the specified string comparison function (see
    compare_strings for more details) as well as a
    scoring threshold the comparison must meet or exceed.

    :param record_i: One of the records in the candidate pair to evaluate.
    :param record_j: The second record in the candidate pair.
    :param feature_col: The name of the column being evaluated (e.g. "city").
    :param col_to_idx: A dictionary mapping column names to the numeric index
      in which they occur in order in the data.
    :param **kwargs: Optionally, a dictionary including specifications for
      the string comparison metric to use, as well as the cutoff score
      beyond which to classify the strings as a partial match.
    :return: A boolean indicating whether the features are a fuzzy match.
    """
    idx = col_to_idx[feature_col]

    # Convert datetime obj to str using helper function
    if feature_col == "birthdate":
        record_i[idx] = utils.datetime_to_str(record_i[idx])
        record_j[idx] = utils.datetime_to_str(record_j[idx])

    # Special case for two empty strings, since we don't want vacuous
    # equality (or in-) to penalize the score
    if record_i[idx] == "" and record_j[idx] == "":
        return True
    if record_i[idx] is None and record_j[idx] is None:
        return True

    similarity_measure, threshold = _get_fuzzy_params(feature_col, **kwargs)
    score = compare_strings(record_i[idx], record_j[idx], similarity_measure)
    return score >= threshold


def feature_match_log_odds_exact(
    record_i: list,
    record_j: list,
    feature_col: str,
    col_to_idx: dict[str, int],
    **kwargs: dict,
) -> float:
    """
    Determines whether two feature values in two records should earn the full
    log-odds similarity score (i.e. they match exactly) or whether they
    should earn no weight (they differ). Used for fields for which fuzzy
    comparisons are inappropriate, such as sex.

    :param record_i: One of the records in the candidate pair to evaluate.
    :param record_j: The second record in the candidate pair.
    :param feature_col: The name of the column being evaluated (e.g. "city").
    :param col_to_idx: A dictionary mapping column names to the numeric index
      in which they occur in order in the data.
    :return: A float of the score the feature comparison earned.
    """
    if "log_odds" not in kwargs:
        raise KeyError("Mapping of columns to m/u log-odds must be provided.")
    col_odds = kwargs["log_odds"][feature_col]
    idx = col_to_idx[feature_col]
    if record_i[idx] == record_j[idx]:
        return col_odds
    else:
        return 0.0


def feature_match_log_odds_fuzzy_compare(
    record_i: list,
    record_j: list,
    feature_col: str,
    col_to_idx: dict[str, int],
    **kwargs: dict,
) -> float:
    """
    Determines the weighted string-odds similarly score earned by two
    feature values in two records, as a function of the pre-computed
    log-odds weights and the string similarity between the two features.
    This scales the full score that would be earned from a perfect
    match to a degree of partial weight appropriate to how similar the
    two strings are.

    :param record_i: One of the records in the candidate pair to evaluate.
    :param record_j: The second record in the candidate pair.
    :param feature_col: The name of the column being evaluated (e.g. "city").
    :param col_to_idx: A dictionary mapping column names to the numeric index
      in which they occur in order in the data.
    :return: A float of the score the feature comparison earned.
    """
    if "log_odds" not in kwargs:
        raise KeyError("Mapping of columns to m/u log-odds must be provided.")
    col_odds = kwargs["log_odds"][feature_col]
    idx = col_to_idx[feature_col]

    # Convert datetime obj to str using helper function
    if feature_col == "birthdate":
        record_i[idx] = utils.datetime_to_str(record_i[idx])
        record_j[idx] = utils.datetime_to_str(record_j[idx])

    similarity_measure, threshold = _get_fuzzy_params(feature_col, **kwargs)
    score = compare_strings(record_i[idx], record_j[idx], similarity_measure)
    if score < threshold:
        score = 0.0
    return score * col_odds


def match_within_block(
    block: list[list],
    feature_funcs: dict[str, typing.Callable],
    col_to_idx: dict[str, int],
    match_eval: typing.Callable,
    **kwargs,
) -> list[tuple]:
    """
    Performs matching on all candidate pairs of records within a given block
    of data. Actual partitioning of the data should be done outside this
    function, as it compares all possible pairs within the provided partition.
    Uses a given construction of feature comparison rules as well as a
    match evaluation rule to determine the final verdict on whether two
    records are indeed a match.

    A feature function is of the form "feature_match_X" for some condition
    X; it must accept two records (lists of data), an index i in which the
    feature to compare is stored, and the parameter **kwargs. It must return
    a boolean indicating whether the features "match" for whatever definition
    of match the function uses (i.e. this allows modular logic to apply to
    different features in the compared records). Note that not all features
    in a record need a comparison function defined.

    A match evaluation rule is a function of the form "eval_X" for some
    condition X. It accepts as input a list of booleans, one for each feature
    that was compared with feature funcs, and determines whether the
    comparisons constitute a match according to X.

    :param block: A list of records to check for matches. Each record in
      the list is itself a list of features. The first feature of the
      record must be an "id" for the record.
    :param feature_funcs: A dictionary mapping feature indices to functions
      used to evaluate those features for a match.
    :param col_to_idx: A dictionary mapping column names to the numeric index
      in which they occur in order in the data.
    :param match_eval: A function for determining whether a given set of
      feature comparisons constitutes a match for linkage.
    :return: A list of 2-tuples of the form (i,j), where i,j give the indices
      in the block of data of records deemed to match.
    """
    match_pairs: list[tuple] = []

    # Dynamic programming table: order doesn't matter, so only need to
    # check each combo of i,j once
    for i, record_i in enumerate(block):
        for j in range(i + 1, len(block)):
            record_j = block[j]
            feature_comps = [
                feature_funcs[feature_col](
                    record_i, record_j, feature_col, col_to_idx, **kwargs
                )
                for feature_col in feature_funcs
            ]

            # If it's a match, store the result
            is_match = match_eval(feature_comps, **kwargs)
            if is_match:
                match_pairs.append((i, j))

    return match_pairs


def match_within_block_cluster_ratio(
    block: list[list],
    cluster_ratio: float,
    feature_funcs: dict[str, typing.Callable],
    col_to_idx: dict[str, int],
    match_eval: typing.Callable,
    **kwargs,
) -> list[set]:
    """
    A matching function for statistically testing the impact of membership
    ratio to the quality of clusters formed. This function behaves similarly
    to `match_within_block`, except that rather than identifying all pairwise
    candidates which are deemed matches, the function creates a list of
    clusters of patients, where each cluster constitutes what would be a
    single "representative" patient in the database. The formation of
    clusters is determined by the parameter `cluster_ratio`, which defines
    the proportion of other records in an existing cluster that a new
    incoming record must match in order to join the cluster.

    :param block: A list of records to check for matches. Each record in
      the list is itself a list of features. The first feature of the
      record must be an "id" for the record.
    :param cluster_ratio: A float giving the proportion of records in an
      existing cluster that a new incoming record must match in order
      to qualify for membership in the cluster.
    :param feature_funcs: A dictionary mapping feature indices to functions
      used to evaluate those features for a match.
    :param col_to_idx: A dictionary mapping column names to the numeric index
      in which they occur in order in the data.
    :param match_eval: A function for determining whether a given set of
      feature comparisons constitutes a match for linkage.
    :return: A list of 2-tuples of the form (i,j), where i,j give the indices
      in the block of data of records deemed to match.
    """
    clusters: list[set] = []
    for i in range(len(block)):
        # Base case
        if len(clusters) == 0:
            clusters.append({i})
            continue
        found_master_cluster = False

        # Iterate through clusters to find one that we match with
        for cluster in clusters:
            belongs = _eval_record_in_cluster(
                block,
                i,
                cluster,
                cluster_ratio,
                feature_funcs,
                col_to_idx,
                match_eval,
                **kwargs,
            )
            if belongs:
                found_master_cluster = True
                cluster.add(i)
                break

        # Create a new singleton if no other cluster qualified
        if not found_master_cluster:
            clusters.append({i})
    return clusters


def _eval_record_in_cluster(
    block: list[list],
    i: int,
    cluster: set,
    cluster_ratio: float,
    feature_funcs: dict[str, typing.Callable],
    col_to_idx: dict[str, int],
    match_eval: typing.Callable,
    **kwargs,
) -> bool:
    """
    A helper function used to evaluate whether a given incoming record
    satisfies the matching proportion threshold of an existing cluster,
    and therefore would belong to the cluster.
    """
    record_i = block[i]
    num_matched = 0.0
    for j in cluster:
        record_j = block[j]
        feature_comps = [
            feature_funcs[feature_col](
                record_i, record_j, feature_col, col_to_idx, **kwargs
            )
            for feature_col in feature_funcs
        ]

        is_match = match_eval(feature_comps)
        if is_match:
            num_matched += 1.0

    return (num_matched / len(cluster)) >= cluster_ratio


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

    threshold: float = 0.7
    if "thresholds" in kwargs:
        if col in kwargs["thresholds"]:
            threshold = kwargs["thresholds"][col]
    elif "threshold" in kwargs:
        threshold = kwargs["threshold"]

    return (similarity_measure, threshold)

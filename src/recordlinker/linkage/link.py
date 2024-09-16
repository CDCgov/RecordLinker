import datetime
import hashlib
import json
import logging
import pathlib
from typing import Union

from pydantic import Field

from recordlinker.linkage import utils
from recordlinker.linkage.mpi import BaseMPIConnectorClient
from recordlinker.linkage.mpi import DIBBsMPIConnectorClient

LINKING_FIELDS_TO_FHIRPATHS = {
    "first_name": "Patient.name.given",
    "last_name": "Patient.name.family",
    "birthdate": "Patient.birthDate",
    "address": "Patient.address.line",
    "zip": "Patient.address.postalCode",
    "city": "Patient.address.city",
    "state": "Patient.address.state",
    "sex": "Patient.gender",
    "mrn": "Patient.identifier.where(type.coding.code='MR').value",
}


def compile_match_lists(match_lists: list[dict], cluster_mode: bool = False):
    """
    Turns a list of matches of either clusters or candidate pairs found
    during linkage into a single unified structure holding all found matches
    across all rules passes. E.g. if a single pass of a linkage algorithm
    uses three rules, hence generates three dictionaries of matches, this
    function will aggregate the results of those three separate dicts into
    a single unified and deduplicated dictionary. For consistency during
    statistical evaluation, the returned dictionary is always indexed by
    the lower ID of the records in a given pair.

    :param match_lists: A list of the dictionaries obtained during a run
      of the linkage algorithm, one dictionary per rule used in the run.
    :param cluster_mode: An optional boolean indicating whether the linkage
      algorithm was run in cluster mode. Default is False.
    :return: The aggregated dictionary of unified matches.
    """
    matches = {}
    for matches_from_rule in match_lists:
        for matches_within_blocks in matches_from_rule.values():
            for candidate_set in matches_within_blocks:
                # Always index the aggregate by the lowest valued ID
                # for statistical consistency and deduplication
                root_record = min(candidate_set)
                if root_record not in matches:
                    matches[root_record] = set()

                # For clustering, need to add all other records in the cluster
                if cluster_mode:
                    for clustered_record in candidate_set:
                        if clustered_record != root_record:
                            matches[root_record].add(clustered_record)
                else:
                    matched_record = max(candidate_set)
                    matches[root_record].add(matched_record)
    return matches


def extract_blocking_values_from_record(
    record: dict, blocking_fields: list[dict]
) -> dict:
    """
    Extracts values from a given patient record for eventual use in database
    record linkage blocking. A list of fields to block on, as well as a mapping
    of those fields to any desired transformations of their extracted values,
    is used to fhir-path parse the value out of the incoming patient record.

    Currently supported blocking fields:
    - first_name
    - last_name
    - birthdate
    - address
    - city
    - state
    - zip
    - sex
    - mrn

    Currently supported transformations on extracted fields:
    - first4: the first four characters of the value
    - last4: the last four characters of the value

    :param record: A FHIR-formatted Patient record.
    :param blocking_fields: A List of dictionaries giving the blocking
      fields and any transformations that should be applied to them. Each
      dictionary in the list should include a "value" key with one of the
      supported blocking fields above, and may also optionally contain a
      "transformation" key whose value is one of our supported transforms.
    """

    transform_funcs = {
        "first4": lambda x: x[:4] if len(x) >= 4 else x,
        "last4": lambda x: x[-4:] if len(x) >= 4 else x,
    }

    for block_dict in blocking_fields:
        if "value" not in block_dict:
            raise KeyError(
                f"Input dictionary for block {block_dict} must contain a 'value' key."
            )

    block_vals = dict.fromkeys([b.get("value") for b in blocking_fields], "")
    transform_blocks = [b for b in blocking_fields if "transformation" in b]
    transformations = dict(
        zip(
            [b.get("value") for b in transform_blocks],
            [b.get("transformation") for b in transform_blocks],
        )
    )
    for block_dict in blocking_fields:
        block = block_dict.get("value")
        try:
            # Apply utility extractor for safe parsing
            value = utils.extract_value_with_resource_path(
                record,
                LINKING_FIELDS_TO_FHIRPATHS[block],
                selection_criteria="first",
            )
            if value:
                if block in transformations:
                    try:
                        value = transform_funcs[transformations[block]](value)
                    except KeyError:
                        raise ValueError(
                            f"Transformation {transformations[block]} is not valid."
                        )
                    block_vals[block] = {
                        "value": value,
                        "transformation": transformations[block],
                    }
                else:
                    block_vals[block] = {"value": value}

        except KeyError:
            raise ValueError(f"Field {block} is not a supported extraction field.")

    # Account for any incoming FHIR resources that return no data
    # for a field--don't count this against records to-block
    keys_to_pop = []
    for field in block_vals:
        if _is_empty_extraction_field(block_vals, field):
            keys_to_pop.append(field)
    for k in keys_to_pop:
        block_vals.pop(k)

    return block_vals


def generate_hash_str(linking_identifier: str, salt_str: str) -> str:
    """
    Generates a hash for a given string of concatenated patient information. The hash
    serves as a "unique" identifier for the patient.

    :param linking_identifier: The value to be hashed.  For example, the concatenation
      of a patient's name, address, and date of birth, delimited by dashes.
    :param salt_str: The salt to use with the hash. This is intended to prevent
      reverse engineering of the PII used to create the hash.
    :return: The hash of the linking_identifier string.
    """
    hash_obj = hashlib.sha256()
    to_encode = (linking_identifier + salt_str).encode("utf-8")
    hash_obj.update(to_encode)
    return hash_obj.hexdigest()


def link_record_against_mpi(
    record: dict,
    algo_config: list[dict],
    external_person_id: str = None,
    mpi_client: BaseMPIConnectorClient = None,
) -> tuple[bool, str]:
    """
    Runs record linkage on a single incoming record (extracted from a FHIR
    bundle) using an existing database as an MPI. Uses a flexible algorithm
    configuration to allow customization of the exact kind of linkage to
    run. Linkage is assumed to run using cluster membership (i.e. the new
    record must match a certain proportion of existing records all assigned
    to a person in order to match), and if multiple persons are matched,
    the new record is linked to the person with the strongest membership
    percentage.

    :param record: The FHIR-formatted patient resource to try to match to
      other records in the MPI.
    :param algo_config: An algorithm configuration consisting of a list
      of dictionaries describing the algorithm to run. See
      `read_linkage_config` and `write_linkage_config` for more details.
    :returns: A tuple consisting of a boolean indicating whether a match
      was found for the new record in the MPI, followed by the ID of the
      Person entity now associated with the incoming patient (either a
      new Person ID or the ID of an existing matched Person).
    """
    # Initialize MPI client
    if mpi_client is None:
        logging.info("MPI client was None, instatiating new client.")
        mpi_client = DIBBsMPIConnectorClient()

    # Need to bind function names back to their symbolic invocations
    # in context of the module--i.e. turn the string of a function
    # name back into the callable defined in link.py
    algo_config = [utils.bind_functions(linkage_pass) for linkage_pass in algo_config]

    # Membership ratios need to persist across linkage passes so that we can
    # find the highest scoring match across all trials
    linkage_scores = {}
    for linkage_pass in algo_config:
        blocking_fields = linkage_pass["blocks"]

        # MPI will be able to find patients if *any* of their names or addresses
        # contains extracted values, so minimally block on the first line
        # if applicable
        logging.info(
            f"Starting extract_blocking_values_from_record at:{datetime.datetime.now().strftime('%m-%d-%yT%H:%M:%S.%f')}"  # noqa
        )
        blocking_criteria = extract_blocking_values_from_record(record, blocking_fields)
        logging.info(
            f"Done with extract_blocking_values_from_record at:{datetime.datetime.now().strftime('%m-%d-%yT%H:%M:%S.%f')}"  # noqa
        )

        # We don't enforce blocking if an extracted value is empty, so if all
        # values come back blank, skip the pass because the only alt is comparing
        # to all found records
        if len(blocking_criteria) == 0:
            logging.info("No blocking criteria extracted from incoming record.")
            continue
        logging.info(
            f"Starting get_block_data at: {datetime.datetime.now().strftime('%m-%d-%yT%H:%M:%S.%f')}"  # noqa
        )
        raw_data_block = mpi_client.get_block_data(blocking_criteria)
        logging.info(
            f"Done with get_block_data at: {datetime.datetime.now().strftime('%m-%d-%yT%H:%M:%S.%f')}"  # noqa
        )

        data_block = _convert_given_name_to_first_name(raw_data_block)

        # First row of returned block is column headers
        # Map column name to idx, not including patient/person IDs
        col_to_idx = {v: k for k, v in enumerate(data_block[0][2:])}
        if len(data_block[1:]) > 0:  # Check if data_block is empty
            data_block = data_block[1:]
            logging.info(
                f"Starting _flatten_patient_resource at:{datetime.datetime.now().strftime('%m-%d-%yT%H:%M:%S.%f')}"  # noqa
            )
            flattened_record = _flatten_patient_resource(record, col_to_idx)
            logging.info(
                f"Done with _flatten_patient_resource at:{datetime.datetime.now().strftime('%m-%d-%yT%H:%M:%S.%f')}"  # noqa
            )

            logging.info(
                f"Starting _group_patient_block_by_person at:{datetime.datetime.now().strftime('%m-%d-%yT%H:%M:%S.%f')}"  # noqa
            )
            clusters = _group_patient_block_by_person(data_block)
            logging.info(
                f"Done with _group_patient_block_by_person at:{datetime.datetime.now().strftime('%m-%d-%yT%H:%M:%S.%f')}"  # noqa
            )

            # Check if incoming record should belong to one of the person clusters
            kwargs = linkage_pass.get("kwargs", {})
            for person in clusters:
                num_matched_in_cluster = 0.0
                for linked_patient in clusters[person]:
                    logging.info(
                        f"Starting _compare_records at:{datetime.datetime.now().strftime('%m-%d-%yT%H:%M:%S.%f')}"  # noqa
                    )
                    is_match = _compare_records(
                        flattened_record,
                        linked_patient,
                        linkage_pass["funcs"],
                        col_to_idx,
                        linkage_pass["matching_rule"],
                        **kwargs,
                    )
                    logging.info(
                        f"Done with _compare_records at:{datetime.datetime.now().strftime('%m-%d-%yT%H:%M:%S.%f')}"  # noqa
                    )

                    if is_match:
                        num_matched_in_cluster += 1.0

                # Update membership score for this person cluster so that we can
                # track best possible link across multiple passes
                logging.info(
                    f"Starting to update membership score at:{datetime.datetime.now().strftime('%m-%d-%yT%H:%M:%S.%f')}"  # noqa
                )
                belongingness_ratio = num_matched_in_cluster / len(clusters[person])
                if belongingness_ratio >= linkage_pass.get("cluster_ratio", 0):
                    logging.info(
                        f"belongingness_ratio >= linkage_pass.get('cluster_ratio', 0): {datetime.datetime.now().strftime('%m-%d-%yT%H:%M:%S.%f')}"  # noqa
                    )
                    if person in linkage_scores:
                        linkage_scores[person] = max(
                            [linkage_scores[person], belongingness_ratio]
                        )
                    else:
                        linkage_scores[person] = belongingness_ratio
                logging.info(
                    f"Done with updating membership score at: {datetime.datetime.now().strftime('%m-%d-%yT%H:%M:%S.%f')}"  # noqa
                )
    person_id = None
    matched = False

    # If we found any matches, find the strongest one
    if len(linkage_scores) != 0:
        logging.info(
            f"Starting _find_strongest_link at: {datetime.datetime.now().strftime('%m-%d-%yT%H:%M:%S.%f')}"  # noqa
        )
        person_id = _find_strongest_link(linkage_scores)
        matched = True
        logging.info(
            f"Done with _find_strongest_link at:{datetime.datetime.now().strftime('%m-%d-%yT%H:%M:%S.%f')}"  # noqa
        )
    logging.info(
        f"Starting mpi_client.insert_matched_patient at:{datetime.datetime.now().strftime('%m-%d-%yT%H:%M:%S.%f')}"  # noqa
    )
    person_id = mpi_client.insert_matched_patient(
        record, person_id=person_id, external_person_id=external_person_id
    )
    logging.info(
        f"Done with mpi_client.insert_matched_patient at:{datetime.datetime.now().strftime('%m-%d-%yT%H:%M:%S.%f')}"  # noqa
    )

    return (matched, person_id)


def load_json_probs(path: pathlib.Path):
    """
    Load a dictionary of probabilities from a JSON-formatted file.
    The probabilities correspond to previously computed m-, u-, or
    log-odds probabilities derived from patient records, with one
    score for each field (column) appearing in the data.

    :param path: The file path to load the data from.
    :return: A dictionary of probability scores, one for each field
      in the data set on which they were computed.
    :raises FileNotFoundError: If a file does not exist at the given
      path.
    :raises JSONDecodeError: If the file cannot be read as valid JSON.
    """
    try:
        with open(path, "r") as file:
            prob_dict = json.load(file)
        return prob_dict
    except FileNotFoundError:
        raise FileNotFoundError(f"The specified file does not exist at {path}.")
    except json.decoder.JSONDecodeError as e:
        raise json.decoder.JSONDecodeError(
            "The specified file is not valid JSON.", e.doc, e.pos
        )


def read_linkage_config(config_file: pathlib.Path) -> list[dict]:
    """
    Reads and generates a record linkage algorithm configuration list from
    the provided filepath, which should point to a JSON file. A record
    linkage configuration list is a list of dictionaries--one for each
    pass in the algorithm it describes--containing information on the
    blocking fields, functions, cluster thresholds, and keyword arguments
    for that pass of the linkage algorithm. For a full example of all the
    components involved in a linkage description structure, see the doc
    string for `write_linkage_config`.

    :param config_file: A `pathlib.Path` string pointing to a JSON file
      that describes the algorithm to decode.
    :return: A list of dictionaries whose values can be passed to the
      various parts of linkage pass function.
    """
    try:
        with open(config_file) as f:
            algo_config = json.load(f)
            return algo_config.get("algorithm", [])
    except FileNotFoundError:
        raise FileNotFoundError(f"No file exists at path {config_file}.")
    except json.decoder.JSONDecodeError as e:
        raise json.decoder.JSONDecodeError(
            "The specified file is not valid JSON.", e.doc, e.pos
        )


def score_linkage_vs_truth(
    found_matches: dict[Union[int, str], set],
    true_matches: dict[Union[int, str], set],
    records_in_dataset: int,
    expand_clusters_pairwise: bool = False,
) -> tuple:
    """
    Compute the statistical qualities of a run of record linkage against
    known true results. This function assumes that matches have already
    been determined by the algorithm, and further assumes that true
    matches have already been identified in the data.

    :param found_matches: A dictionary mapping IDs of records to sets of
      other records which were determined to be a match.
    :param true_matches: A dictionary mapping IDs of records to sets of
      other records which are _known_ to be a true match.
    :param records_in_dataset: The number of records in the original data
      set to-link.
    :param expand_clusters_pairwise: Optionally, whether we need to take
      the cross-product of members within the sets of the match list. This
      parameter only needs to be used if the linkage algorithm was run in
      cluster mode. Default is False.
    :return: A tuple reporting the sensitivity/precision, specificity/recall,
      positive prediction value, and F1 score of the linkage algorithm.
    """

    # If cluster mode was used, only the "master" patient's set will exist
    # Need to expand other permutations for accurate statistics
    if expand_clusters_pairwise:
        new_found_matches = {}
        for root_rec in found_matches:
            if root_rec not in new_found_matches:
                new_found_matches[root_rec] = found_matches[root_rec]
            for paired_record in found_matches[root_rec]:
                if paired_record not in new_found_matches:
                    new_found_matches[paired_record] = set()
                for other_record in found_matches[root_rec]:
                    if other_record > paired_record:
                        new_found_matches[paired_record].add(other_record)
        found_matches = new_found_matches

    # Need division by 2 because ordering is irrelevant, matches are symmetric
    total_possible_matches = (records_in_dataset * (records_in_dataset - 1)) / 2.0
    true_positives = 0.0
    false_positives = 0.0
    false_negatives = 0.0

    for root_record in true_matches:
        if root_record in found_matches:
            true_positives += len(
                true_matches[root_record].intersection(found_matches[root_record])
            )
            false_positives += len(
                found_matches[root_record].difference(true_matches[root_record])
            )
            false_negatives += len(
                true_matches[root_record].difference(found_matches[root_record])
            )
        else:
            false_negatives += len(true_matches[root_record])
    for record in set(set(found_matches.keys()).difference(true_matches.keys())):
        false_positives += len(found_matches[record])

    true_negatives = (
        total_possible_matches - true_positives - false_positives - false_negatives
    )

    print("True Positives:", true_positives)
    print("False Positives:", false_positives)
    print("False Negatives:", false_negatives)

    sensitivity = round(true_positives / (true_positives + false_negatives), 3)
    specificity = round(true_negatives / (true_negatives + false_positives), 3)
    ppv = round(true_positives / (true_positives + false_positives), 3)
    f1 = round(
        (2 * true_positives) / (2 * true_positives + false_negatives + false_positives),
        3,
    )
    return (sensitivity, specificity, ppv, f1)


def write_linkage_config(linkage_algo: list[dict], file_to_write: pathlib.Path) -> None:
    """
    Save a provided algorithm description as a JSON dictionary at the provided
    filepath location. Algorithm descriptions are lists of dictionaries, one
    for each pass of the algorithm, whose keys are parameter values for a
    linkage pass (drawn from the list `"funcs"`, `"blocks"`, `"matching_rule"`,
    and optionally `"cluster_ratio"` and `"kwargs"`) and whose values are
    as follows:

    - `"funcs"` should map to a dictionary mapping column name to the
    name of a function in the DIBBS linkage module (such as
    `feature_match_fuzzy_string`)--note that these are the actual
    functions, not string names of the functions
    - `"blocks"` should map to a list of columns to block on (e.g.
    ["MRN4", "ADDRESS4"])
    - `"matching_rule"` should map to one of the evaluation rule functions
    in the DIBBS linkage module (i.e. `eval_perfect_match`)
    - `"cluster_ratio"` should map to a float, if provided
    - `"kwargs"` should map to a dictionary of keyword arguments and their
    associated values, if provided

    :param linkage_algo: A list of dictionaries whose key-value pairs correspond
      to the rules above.
    :param file_to_write: The path to the destination JSON file to write.
    """
    algo_json = []
    for rl_pass in linkage_algo:
        pass_json = {}
        pass_json["funcs"] = {col: f.__name__ for (col, f) in rl_pass["funcs"].items()}
        pass_json["blocks"] = rl_pass["blocks"]
        pass_json["matching_rule"] = rl_pass["matching_rule"].__name__
        if rl_pass.get("cluster_ratio", None) is not None:
            pass_json["cluster_ratio"] = rl_pass["cluster_ratio"]
        if rl_pass.get("kwargs", None) is not None:
            pass_json["kwargs"] = {
                kwarg: val for (kwarg, val) in rl_pass.get("kwargs", {}).items()
            }
        algo_json.append(pass_json)
    linkage_json = {"algorithm": algo_json}
    with open(file_to_write, "w") as out:
        out.write(json.dumps(linkage_json))


def _compare_records(
    record: list,
    mpi_patient: list,
    feature_funcs: dict,
    col_to_idx: dict[str, int],
    matching_rule: callable,
    **kwargs,
) -> bool:
    """
    Helper method that compares the flattened form of an incoming new
    patient record to the flattened form of a patient record pulled
    from the MPI.
    """
    # Format is patient_id, person_id, alphabetical list of FHIR keys
    # Don't use the first two ID cols when linking
    feature_comps = [
        _compare_records_field_helper(
            record[2:],
            mpi_patient[2:],
            feature_col,
            col_to_idx,
            feature_funcs,
            **kwargs,
        )
        for feature_col in feature_funcs
    ]
    is_match = matching_rule(feature_comps, **kwargs)
    return is_match


def _compare_records_field_helper(
    record: list,
    mpi_patient: list,
    feature_col: str,
    col_to_idx: dict[str, int],
    feature_funcs: dict,
    **kwargs,
) -> bool:
    if feature_col == "first_name":
        return _compare_name_elements(
            record, mpi_patient, feature_funcs, feature_col, col_to_idx, **kwargs
        )
    elif feature_col in ["address", "city", "state", "zip"]:
        return _compare_address_elements(
            record, mpi_patient, feature_funcs, feature_col, col_to_idx, **kwargs
        )
    else:
        return feature_funcs[feature_col](
            record, mpi_patient, feature_col, col_to_idx, **kwargs
        )


def _compare_address_elements(
    record: list,
    mpi_patient: list,
    feature_funcs: dict,
    feature_col: str,
    col_to_idx: dict[str, int],
    **kwargs,
) -> bool:
    """
    Helper method that compares all elements from the flattened form of an incoming
    new patient record to all elements of the flattened patient record pulled from
    the MPI.
    """
    feature_comp = False
    idx = col_to_idx[feature_col]
    for r in record[idx]:
        feature_comp = feature_funcs[feature_col](
            [r], [mpi_patient[idx]], feature_col, {feature_col: 0}, **kwargs
        )
        if feature_comp:
            break
    return feature_comp


def _compare_name_elements(
    record: list,
    mpi_patient: list,
    feature_funcs: dict,
    feature_col: str,
    col_to_idx: dict[str, int],
    **kwargs,
) -> bool:
    """
    Helper method that compares all elements from the flattened form of an incoming
    new patient record's name(s) to all elements of the flattened
    patient's name(s) pulled from the MPI.
    """
    idx = col_to_idx[feature_col]
    feature_comp = feature_funcs[feature_col](
        [" ".join(record[idx])],
        [mpi_patient[idx]],
        feature_col,
        {feature_col: 0},
        **kwargs,
    )
    return feature_comp


def _condense_extract_address_from_resource(resource: dict, field: str):
    """
    Formatting function to account for patient resources that have multiple
    associated addresses. Each address is a self-contained object, replete
    with its own `line` property that can hold a list of strings. This
    function condenses that `line` into a single concatenated string, for
    each address object, and returns the result in a properly formatted
    list.
    """
    expanded_address_fhirpath = LINKING_FIELDS_TO_FHIRPATHS[field]
    expanded_address_fhirpath = ".".join(expanded_address_fhirpath.split(".")[:-1])
    list_of_address_objects = utils.extract_value_with_resource_path(
        resource, expanded_address_fhirpath, "all"
    )
    if field == "address":
        list_of_address_lists = [
            ao.get(LINKING_FIELDS_TO_FHIRPATHS[field].split(".")[-1], [])
            for ao in list_of_address_objects
        ]
        list_of_usable_address_elements = [
            " ".join(obj) for obj in list_of_address_lists
        ]
    else:
        list_of_usable_address_elements = []
        for address_object in list_of_address_objects:
            list_of_usable_address_elements.append(
                address_object.get(LINKING_FIELDS_TO_FHIRPATHS[field].split(".")[-1])
            )
    return list_of_usable_address_elements


def _find_strongest_link(linkage_scores: dict) -> str:
    """
    Helper method that determines the highest belongingness level that an
    incoming record achieved against a set of clusers based on existing
    patient records in the MPI. The cluster with the highest belongingness
    ratio is chosen as the Person to link the new record to.
    """
    best_person = max(linkage_scores, key=linkage_scores.get)
    return best_person


def _flatten_patient_resource(resource: dict, col_to_idx: dict) -> list:
    """
    Helper method that flattens an incoming patient resource into a list whose
    elements are the keys of the FHIR dictionary, reformatted and ordered
    according to our "blocking fields extractor" dictionary.
    """
    flattened_record = [
        _flatten_patient_field_helper(resource, f) for f in col_to_idx.keys()
    ]
    flattened_record = [resource["id"], None] + flattened_record
    return flattened_record


def _flatten_patient_field_helper(resource: dict, field: str) -> any:
    """
    Helper function that determines the correct way to flatten a patient's
    FHIR field based on the specific field in question. Names and Addresses,
    because their lists can hold multiple objects, are fetched completely,
    whereas other fields just have their first element used (since historical
    information doesn't matter there).

    For any field for which the value would be `None`, instead use an empty string
    (if the field isn't first_name or address) or a list with one element, the
    empty string (if the field is first_name or address). This ensures that
    future loops over the elements don't disrupt the flow of the matching
    algorithm.
    """
    if field == "first_name":
        vals = utils.extract_value_with_resource_path(
            resource, LINKING_FIELDS_TO_FHIRPATHS[field], selection_criteria="all"
        )
        return vals if vals is not None else [""]
    elif field in ["address", "city", "zip", "state"]:
        vals = _condense_extract_address_from_resource(resource, field)
        return vals if vals is not None else [""]
    else:
        val = utils.extract_value_with_resource_path(
            resource, LINKING_FIELDS_TO_FHIRPATHS[field], selection_criteria="first"
        )
        return val if val is not None else ""


def _group_patient_block_by_person(data_block: list[list]) -> dict[str, list]:
    """
    Helper method that partitions the block of patient data returned from the MPI
    into clusters of records according to their linked Person ID.
    """
    clusters = {}
    for mpi_patient in data_block:
        # Format is patient_id, person_id, alphabetical list of FHIR keys
        if mpi_patient[1] not in clusters:
            clusters[mpi_patient[1]] = []
        clusters[mpi_patient[1]].append(mpi_patient)
    return clusters


def _map_matches_to_record_ids(
    match_list: Union[list[tuple], list[set]], data_block, cluster_mode: bool = False
) -> list[tuple]:
    """
    Helper function to turn a list of tuples of row indices in a block
    of data into a list of tuples of the IDs of the records within
    that block.
    """
    matched_records = []

    # Assumes ID is last column in data set
    if cluster_mode:
        for cluster in match_list:
            new_cluster = set()
            for record_idx in cluster:
                new_cluster.add(data_block[record_idx][-1])
            matched_records.append(new_cluster)
    else:
        for matching_pair in match_list:
            id_i = data_block[matching_pair[0]][-1]
            id_j = data_block[matching_pair[1]][-1]
            matched_records.append((id_i, id_j))
    return matched_records


def _is_empty_extraction_field(block_vals: dict, field: str):
    """
    Helper method that determines when a field extracted from an incoming
    record should be considered "empty" for the purpose of blocking.
    Fields whose values are either `None` or the empty string should not
    be used when retrieving blocked records from the MPI, since that
    would impose an artificial constraint (e.g. if an incoming record
    has no `last_name` field, we don't want to retrieve only records
    from the MPI that also have no `last_name`).
    """
    # Means the value extractor found no data in the FHIR resource
    if block_vals[field] == "":
        return True
    # Alternatively, there was "data" there, but it's empty
    elif (
        block_vals[field].get("value") is None
        or block_vals[field].get("value") == ""
        or block_vals[field].get("value") == [""]
    ):
        return True  # pragma: no cover
    return False


def _write_prob_file(prob_dict: dict, file_to_write: Union[pathlib.Path, None]):
    """
    Helper method to write a probability dictionary to a JSON file, if
    a valid path is supplied.

    :param prob_dict: A dictionary mapping column names to the log-probability
      values computed for those columns.
    :param file_to_write: Optionally, a path variable indicating where to
      write the probabilities in a JSON format. Default is None (meaning this
      function would execute nothing.)
    """
    if file_to_write is not None:
        with open(file_to_write, "w") as out:
            out.write(json.dumps(prob_dict))


def add_person_resource(
    person_id: str, patient_id: str, bundle: dict = Field(description="A FHIR bundle")
) -> dict:
    """
    Adds a simplified person resource to a bundle if the patient resource in the bundle
    matches an existing record in the Master Patient Index. Returns the bundle with
    the newly added person resource.

    :param person_id: _description_
    :param patient_id: _description_
    :param bundle: _description_, defaults to Field(description="A FHIR bundle")
    :return: _description_
    """
    person_resource = {
        "fullUrl": f"urn:uuid:{person_id}",
        "resource": {
            "resourceType": "Person",
            "id": f"{person_id}",
            "link": [{"target": {"reference": f"Patient/{patient_id}"}}],
        },
        "request": {
            "method": "PUT",
            "url": f"Person/{person_id}",
        },
    }

    bundle.get("entry", []).append(person_resource)

    return bundle


def _convert_given_name_to_first_name(data: list[list]) -> list[list]:
    """
    In the list of query row results, convert the given_name column (which is a
    list of given names) to a first_name column (which is a space-delimited string
    of given names).

    :param data: List of lists block data.
    :return: List of lists with first_name column.
    """
    result = []
    if not data:
        return result  # empty list, should return an empty list

    if "given_name" not in data[0]:
        return data  # given_name not in data, should return the original

    given_name_idx = data[0].index("given_name")
    for idx, row in enumerate(data):
        val = "first_name" if idx == 0 else " ".join(row[given_name_idx])
        result.append(row[:given_name_idx] + [val] + row[given_name_idx + 1 :])
    return result

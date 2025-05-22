import copy
import random

from . import config
from . import utils


def scramble_field(data: dict, field: str):
    if field == "FIRST":
        data["name"][0]["given"][0] = utils.apply_field_scrambling(data["name"][0]["given"][0])
    elif field == "LAST":
        data["name"][0]["family"] = utils.apply_field_scrambling(data["name"][0]["family"])
    elif field == "SUFFIX":
        data["name"][0]["suffix"] = utils.apply_field_scrambling(data["name"][0]["suffix"])
    elif field == "GENDER":
        data["sex"] = utils.apply_field_scrambling(data["sex"])
    elif field == "BIRTHDATE":
        data["birth_date"] = utils.apply_field_scrambling(data["birth_date"])
    elif field == "ADDRESS":
        data["address"][0]["line"][0] = utils.apply_field_scrambling(data["address"][0]["line"][0])
    elif field == "CITY":
        data["address"][0]["city"] = utils.apply_field_scrambling(data["address"][0]["city"])
    elif field == "ZIP":
        data["address"][0]["postal_code"] = utils.apply_field_scrambling(
            data["address"][0]["postal_code"]
        )
    elif field == "SSN":
        if data["identifiers"]:
            for identifier in data["identifiers"]:
                if identifier["type"] == "SS":
                    identifier["value"] = utils.apply_field_scrambling(identifier["value"])
    elif field == "MRN":
        if data["identifiers"]:
            for identifier in data["identifiers"]:
                if identifier["type"] == "MR":
                    identifier["value"] = utils.apply_field_scrambling(identifier["value"])
    return data


def scramble(data: dict) -> dict:
    """
    Scrambles a subset of relevant fields and returns the scrambled dict.
    """

    # TODO: Move prep to its own function
    seed_cluster = copy.deepcopy(data)
    original_records = data["records"][:]
    for record in original_records:
        # Generate and add scrambled duplicates
        for _ in range(random.randint(config.MIN_DUPLICATE_CASES, config.MAX_DUPLICATE_CASES)):
            dupe = copy.deepcopy(record)
            # Determine if this duplicate will be subject to field dropout
            missing_fields_in_case = utils.identify_missing_fields(record, json_get_field)
            acceptable_fields_to_drop = [
                f for f in config.ALGORITHM_RELEVANT_COLUMNS if f not in missing_fields_in_case
            ]
            fields_to_drop = []
            if random.random() < config.CHANCE_TO_DROP_FIELDS:
                # Randomly determine fields to drop from this duplicate, only dropping
                # fields that weren't already dropped in the original test case
                fields_to_drop = random.sample(
                    acceptable_fields_to_drop,
                    random.randint(config.MIN_FIELDS_TO_DROP, config.MAX_FIELDS_TO_DROP),
                )
                for f in fields_to_drop:
                    # Set the field to an empty string to simulate missingness
                    utils.set_field(f, "", dupe, json_set_field)

            # Determine if this duplicate will be subject to field scrambling
            if random.random() < config.CHANCE_TO_SCRAMBLE:
                # Determine which fields are safe to scramble (can't be missing)
                safe_to_scramble = [f for f in acceptable_fields_to_drop if f not in fields_to_drop]
                fields_to_scramble = utils.select_fields_to_scramble(safe_to_scramble)
                for field in fields_to_scramble:
                    dupe = scramble_field(dupe, field)
            seed_cluster["records"].append(dupe)
        # Randomize the order of records in the cluster to avoid order bias
        # and to ensure that the original record is not always first
        random.shuffle(seed_cluster["records"])

    return seed_cluster


def json_get_field(field: str, data: dict) -> str | None:
    """
    Get the value of a field from a JSON object.
    """
    try:
        if field == "FIRST":
            return data["name"][0]["given"][0]
        elif field == "LAST":
            return data["name"][0]["family"]
        elif field == "SUFFIX":
            return data["name"][0]["suffix"]
        elif field == "GENDER":
            return data["sex"]
        elif field == "BIRTHDATE":
            return data["birth_date"]
        elif field == "ADDRESS":
            return data["address"][0]["line"][0]
        elif field == "CITY":
            return data["address"][0]["city"]
        elif field == "ZIP":
            return data["address"][0]["postal_code"]
        elif field == "SSN":
            for identifier in data.get("identifiers", []):
                if identifier["type"] == "SS":
                    return identifier["value"]
        elif field == "MRN":
            for identifier in data.get("identifiers", []):
                if identifier["type"] == "MR":
                    return identifier["value"]
    except (KeyError, IndexError):
        return None
    return None


def json_set_field(field: str, data: dict, value: str) -> str | None:
    """
    Get the value of a field from a JSON object.
    """
    try:
        if field == "FIRST":
            data["name"][0]["given"][0] = value
        elif field == "LAST":
            data["name"][0]["family"] = value
        elif field == "SUFFIX":
            data["name"][0]["suffix"] = value
        elif field == "GENDER":
            data["sex"] = value
        elif field == "BIRTHDATE":
            data["birth_date"] = value
        elif field == "ADDRESS":
            data["address"][0]["line"][0] = value
        elif field == "CITY":
            data["address"][0]["city"] = value
        elif field == "ZIP":
            data["address"][0]["postal_code"] = value
        elif field == "SSN":
            for identifier in data.get("identifiers", []):
                if identifier["type"] == "SS":
                    identifier["value"] = value
                    break
        elif field == "MRN":
            for identifier in data.get("identifiers", []):
                if identifier["type"] == "MR":
                    identifier["value"] = value
                    break
    except KeyError:
        pass

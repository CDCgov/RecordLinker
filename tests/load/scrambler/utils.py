import datetime
import random
import string
import typing

from . import config


def apply_field_scrambling(value: str) -> str:
    if not value:
        return value
    ## TODO: use argparse to get min and max edit distance
    edits = random.randint(config.MIN_EDIT_DISTANCE, config.MAX_EDIT_DISTANCE)
    chars = list(value)
    for _ in range(edits):
        action = random.choice(["add", "delete", "transpose"])
        if action == "add":
            idx = random.randint(0, len(chars))
            chars.insert(idx, random.choice(string.ascii_letters))
        elif action == "delete" and chars:
            idx = random.randint(0, len(chars) - 1)
            del chars[idx]
        elif action == "transpose" and len(chars) > 1:
            idx = random.randint(0, len(chars) - 2)
            chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
    return "".join(chars)


def apply_date_scrambling(value: str) -> str:
    if not value:
        return value

    original_date = datetime.datetime.strptime(value, "%Y-%m-%d")

    action = random.choice(["year", "month", "day"])
    if action == "month":
        adjustment = random.randint(1, 12) * 30
    elif action == "day":
        adjustment = random.randint(0, 30)
    elif action == "year":
        # Randomly adjust the year by up to 10 years
        adjustment = random.randint(0, 10) * 365

    new_date = original_date - datetime.timedelta(days=adjustment)
    return new_date.strftime("%Y-%m-%d")


def select_fields_to_scramble(fields: list[str]) -> list[str]:
    if not fields:
        return []

    num_fields = random.randint(
        min(len(fields), config.MIN_FIELDS_TO_SCRAMBLE),
        min(len(fields), config.MAX_FIELDS_TO_SCRAMBLE),
    )
    return random.sample(fields, num_fields)


def get_scramblable_fields(relevant_fields: list[str], get_field_fn) -> list[str]:
    return [field for field in relevant_fields if get_field_fn(field)]


def identify_missing_fields(
    data: dict, get_field_fn: typing.Callable[[str, dict], str | None]
) -> list[str]:
    """
    Identify which fields in a given test case, if any, are missing
    data that might be relevant to the algorithm.
    """
    missing_fields = []
    for field in config.ALGORITHM_RELEVANT_COLUMNS:
        value = get_field_fn(field, data)
        if value in (None, ""):
            missing_fields.append(field)
    return missing_fields


def set_field(
    field: str, value: str, data: dict, set_field_fn: typing.Callable[[str, dict, str], None]
) -> None:
    """
    Generalized setter function for updating a field's value
    in either a CSV-like or JSON-like record.
    """
    set_field_fn(field, data, value)

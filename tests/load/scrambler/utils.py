import random
import string
import typing

# from config import MAX_EDIT_DISTANCE, MIN_EDIT_DISTANCE
# Controls for scrambling the value of feature fields in a test case
# duplicate. For each duplicate generated, there is some probability
# of applying field scrambling. If a duplicate is flagged for scrambling,
# then the number of fields to scramble is randomly selected. For each
# randomly selected field, the number of "quality issues" to be
# applied (as measured by edits including addition, deletion, and
# transposition) is randomly determined from a given range.
MIN_EDIT_DISTANCE = 1
MAX_EDIT_DISTANCE = 2

MIN_FIELDS_TO_SCRAMBLE = 1
MAX_FIELDS_TO_SCRAMBLE = 3

ALGORITHM_RELEVANT_COLUMNS = [
    "BIRTHDATE",
    "FIRST",
    "LAST",
    "SUFFIX",
    "GENDER",
    "ADDRESS",
    "CITY",
    "ZIP",
    "SSN",
    "MRN",
]


def apply_field_scrambling(value: str) -> str:
    if not value:
        return value
    ## TODO: use argparse to get min and max edit distance
    edits = random.randint(MIN_EDIT_DISTANCE, MAX_EDIT_DISTANCE)
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


def select_fields_to_scramble(fields: list[str]) -> list[str]:
    if not fields:
        return []

    num_fields = random.randint(
        min(len(fields), MIN_FIELDS_TO_SCRAMBLE), min(len(fields), MAX_FIELDS_TO_SCRAMBLE)
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
    for field in ALGORITHM_RELEVANT_COLUMNS:
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

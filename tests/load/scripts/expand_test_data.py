import copy
import random
from abc import ABC
from abc import abstractmethod

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
]

# Range of the number of copies to make of each test case, before
# applying scrambling. Value is chosen randomly within the range.
# Note that the range of how many cases you end up with for each
# starting case is this range + 1, since you have the original case
# plus the duplicates (we want to preserve the original test, too)
MIN_DUPLICATE_CASES = 2
MAX_DUPLICATE_CASES = 6

# Controls for the random dropout of field information to simulate
# missingness issues in incoming data. For each duplicate created
# for a test case, there is a desired probability to apply dropout
# to some number of fields in that duplicate. If that duplicate is
# randomly chosen to experience dropout, then a random number of
# fields in the range specified are blanked out.
CHANCE_TO_DROP_FIELDS = 0.5
MIN_FIELDS_TO_DROP = 1
MAX_FIELDS_TO_DROP = 2

# Controls for scrambling the value of feature fields in a test case
# duplicate. For each duplicate generated, there is some probability
# of applying field scrambling. If a duplicate is flagged for scrambling,
# then the number of fields to scramble is randomly selected. For each
# randomly selected field, the number of "quality issues" to be
# applied (as measured by edits including addition, deletion, and
# transposition) is randomly determined from a given range.
CHANCE_TO_SCRAMBLE = 0.5
MIN_FIELDS_TO_SCRAMBLE = 1
MAX_FIELDS_TO_SCRAMBLE = 3
MIN_EDIT_DISTANCE = 1
MAX_EDIT_DISTANCE = 2


def identify_missing_fields(test_case: dict[str, str]) -> list:
    """
    Identify which fields in a given test case, if any, are missing
    data that might be relevant to the algorithm.
    """
    missing_fields = []
    for field in ALGORITHM_RELEVANT_COLUMNS:
        if test_case[field] is None or test_case[field] == "":
            missing_fields.append(field)
    return missing_fields


def apply_field_scrambling(
    test_case: dict[str, str], fields_to_scramble: list[str]
) -> dict[str, str]:
    """
    Apply scrambling to each field selected to be randomized.
    """
    for f in fields_to_scramble:
        base_value = copy.deepcopy(test_case[f])

        # We need to track which changes have already been made so that
        # we don't overwrite them and still count it--e.g. if we transpose
        # two letters, deleting one of those letters isn't a new edit
        char_indexes = list(range(len(base_value)))
        altered_positions = []
        edits_to_apply = []

        # Determine how many random edits to apply
        for _ in range(random.randint(MIN_EDIT_DISTANCE, MAX_EDIT_DISTANCE)):
            # Need to loop until we get a valid edit
            # This prevents overwriting previous work
            made_edit = False
            while not made_edit:
                # Select type of edit to make
                edit = random.choice(["add", "delete", "transpose"])

                # Characteres can be added before each existing character, and
                # at the end of the string
                if edit == "add":
                    add_at = random.randint(0, len(base_value))
                    # Adds are always safe to perform because they don't touch
                    # anything else
                    edits_to_apply.append(("add", add_at, random.choice(string.ascii_letters)))
                    made_edit = True

                elif edit == "delete":
                    safe_spots = [x for x in char_indexes if x not in altered_positions]
                    # Can only safely delete a character not already deleted
                    # or swapped
                    if safe_spots != []:
                        delete_char_at = random.choice(safe_spots)
                        altered_positions.append(delete_char_at)
                        edits_to_apply.append(("delete", delete_char_at))
                        made_edit = True

                elif edit == "transpose":
                    safe_spots = [x for x in char_indexes if x not in altered_positions]
                    # Transpositions are most alteration-intensive, affect two positions
                    # Can only swap them if neither has been edited
                    if safe_spots != []:
                        eligible_swap = False
                        # Make sure we have an eligible transposition before we loop over
                        # generating the appropriate indices
                        for pos in range(len(safe_spots) - 1):
                            if safe_spots[pos] == safe_spots[pos + 1] - 1:
                                eligible_swap = True
                                break

                        # There's at least one place where we can switch two adjacent
                        # characters, so randomly pick one such spot
                        if eligible_swap:
                            valid_trans = False
                            left_swap_at = 0
                            right_swap_at = 0
                            while not valid_trans:
                                left_swap_at = random.choice(safe_spots)
                                right_swap_at = left_swap_at + 1
                                if right_swap_at in safe_spots:
                                    valid_trans = True

                            altered_positions.append(left_swap_at)
                            altered_positions.append(right_swap_at)
                            edits_to_apply.append(("transpose", left_swap_at))
                            made_edit = True

        # Now apply edits to this field
        # We'll work in reverse order of index to avoid interference
        edits_to_apply = sorted(edits_to_apply, key=lambda x: x[1], reverse=True)
        for e in edits_to_apply:
            if e[0] == "add":
                if e[1] < len(base_value):
                    base_value = base_value[: e[1]] + e[2] + base_value[e[1] :]
                # Add to the end, just concatenate
                else:
                    base_value += e[2]

            # Deleting is just splicing out the character
            elif e[0] == "delete":
                if e[1] == len(base_value) - 1:
                    base_value = base_value[: len(base_value) - 1]
                else:
                    base_value = base_value[: e[1]] + base_value[e[1] + 1 :]

            # Python strings are immutable and can't be assigned, so just
            # reconstruct a new string with the letters manually inserted
            else:
                left_char = base_value[e[1]]
                right_char = base_value[e[1] + 1]
                base_value = base_value[: e[1]] + right_char + left_char + base_value[e[1] + 2 :]
        test_case[f] = base_value

    return test_case


class AbstractTestCase(ABC):
    @abstractmethod
    def get_scramblable_fields(self) -> list[str]:
        pass

    @abstractmethod
    def scramble_fields(self, fields: list[str]):
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass


class CSVTestCase(AbstractTestCase):
    def __init__(self, data: dict[str, str]):
        self.data = data

    def get_scramblable_fields(self) -> list[str]:
        return [f for f in ALGORITHM_RELEVANT_COLUMNS if self.data.get(f)]

    def scramble_fields(self, fields: list[str]):
        self.data = apply_field_scrambling(self.data, fields)

    def to_dict(self) -> dict:
        return self.data


class JSONTestCase(AbstractTestCase):
    def __init__(self, data: dict):
        self.data = data

    def _get_field(self, field: str) -> str:
        if field == "FIRST":
            return self.data["name"][0]["given"][0]
        elif field == "LAST":
            return self.data["name"][0]["family"]
        elif field == "SUFFIX":
            return self.data["name"][0]["suffix"][0] if self.data["name"][0]["suffix"] else ""
        elif field == "GENDER":
            return self.data["sex"]
        elif field == "BIRTHDATE":
            return self.data["birth_date"]
        elif field == "ADDRESS":
            return self.data["address"][0]["line"][0]
        elif field == "CITY":
            return self.data["address"][0]["city"]
        elif field == "ZIP":
            return self.data["address"][0]["postal_code"]
        elif field == "SSN":
            if "identifiers" in self.data:
                for identifier in self.data["identifiers"]:
                    if identifier["type"] == "SS":
                        return identifier["value"]
        else:
            return ""

    def _set_field(self, field: str, value: str):
        if field == "FIRST":
            self.data["name"][0]["given"][0] = value
        elif field == "LAST":
            self.data["name"][0]["family"] = value
        elif field == "SUFFIX":
            self.data["name"][0]["suffix"] = [value]
        elif field == "GENDER":
            self.data["sex"] = value
        elif field == "BIRTHDATE":
            self.data["birth_date"] = value
        elif field == "ADDRESS":
            self.data["address"][0]["line"][0] = value
        elif field == "CITY":
            self.data["address"][0]["city"] = value
        elif field == "ZIP":
            self.data["address"][0]["postal_code"] = value
        # FIX THIS
        # elif field == "SSN":
        #     self.data["telecom"][0]["value"] = value

    def get_scramblable_fields(self) -> list[str]:
        return [field for field in ALGORITHM_RELEVANT_COLUMNS if self._get_field(field)]

    def scramble_fields(self, fields: list[str]):
        for field in fields:
            value = self._get_field(field)
            temp_dict = {field: value}
            scrambled = apply_field_scrambling(temp_dict, [field])
            self._set_field(field, scrambled[field])

    def to_dict(self) -> dict:
        return self.data


def expand_test_cases(test_cases: list[AbstractTestCase]) -> list[dict]:
    expanded = []

    for case in test_cases:
        expanded.append(case.to_dict())
        valid_fields = case.get_scramblable_fields()

        for _ in range(random.randint(MIN_DUPLICATE_CASES, MAX_DUPLICATE_CASES)):
            dupe = copy.deepcopy(case)
            fields_to_scramble = random.sample(
                valid_fields,
                min(
                    len(valid_fields),
                    random.randint(MIN_FIELDS_TO_SCRAMBLE, MAX_FIELDS_TO_SCRAMBLE),
                ),
            )
            dupe.scramble_fields(fields_to_scramble)
            expanded.append(dupe.to_dict())

    return expanded

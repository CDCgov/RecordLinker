import random

from .base import BaseScrambler
from .utils import apply_field_scrambling

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


class JSONScrambler(BaseScrambler):
    def __init__(self, data: dict, relevant_fields: list[str]):
        self.data = data
        self.relevant_fields = relevant_fields

    def _get_field(self, field: str) -> str:
        try:
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
                if self.data["identifiers"]:
                    for identifier in self.data["identifiers"]:
                        if identifier["type"] == "SS":
                            return identifier["value"]
            else:
                return ""
        except (KeyError, IndexError):
            return ""

    def _set_field(self, field: str, value: str):
        try:
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
            elif field == "SSN":
                if self.data["identifiers"]:
                    for identifier in self.data["identifiers"]:
                        if identifier["type"] == "SS":
                            identifier["value"] = value
        except (KeyError, IndexError):
            pass

    def scramble(self) -> dict:
        """
        Scrambles a subset of relevant fields and returns the scrambled dict.
        """
        fields_to_scramble = self._get_scramblable_fields()
        fields_to_scramble = self._select_fields_to_scramble(fields_to_scramble)

        for field in fields_to_scramble:
            value = self._get_field(field)
            print(f"Scrambling field: {field} with value: {value}")
            if value:
                scrambled = apply_field_scrambling(value)
                self._set_field(field, scrambled)

        return self.data

    def _get_scramblable_fields(self) -> list[str]:
        return [field for field in self.relevant_fields if self._get_field(field)]

    def _select_fields_to_scramble(self, fields: list[str]) -> list[str]:
        if not fields:
            return []

        num_fields = random.randint(
            min(len(fields), MIN_FIELDS_TO_SCRAMBLE), min(len(fields), MAX_FIELDS_TO_SCRAMBLE)
        )
        return random.sample(fields, num_fields)

    def to_dict(self) -> dict:
        return self.data

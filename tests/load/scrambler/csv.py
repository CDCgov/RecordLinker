import random

from base import BaseScrambler
from utils import apply_field_scrambling

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


class CSVScrambler(BaseScrambler):
    CHANCE_TO_SCRAMBLE = 0.5

    def __init__(self, row: dict, relevant_fields: list[str]):
        self.row = row
        self.relevant_fields = relevant_fields

    def scramble(self) -> dict:
        """
        Scrambles a subset of relevant fields and returns the scrambled row.
        """
        fields_to_scramble = self._get_scramblable_fields()
        fields_to_scramble = self._select_fields_to_scramble(fields_to_scramble)

        for field in fields_to_scramble:
            value = self.row.get(field)
            if value:
                scrambled = apply_field_scrambling({field: value}, [field])
                self.row[field] = scrambled[field]

        return self.row

    def _get_scramblable_fields(self) -> list[str]:
        return [field for field in self.relevant_fields if self.row.get(field)]

    def _select_fields_to_scramble(self, fields: list[str]) -> list[str]:
        candidates = [f for f in fields if random.random() < CHANCE_TO_SCRAMBLE]
        if not candidates:
            candidates = random.sample(fields, k=1)  # ensure at least one

        num_fields = random.randint(
            min(len(candidates), MIN_FIELDS_TO_SCRAMBLE),
            min(len(candidates), MAX_FIELDS_TO_SCRAMBLE),
        )
        return random.sample(candidates, num_fields)

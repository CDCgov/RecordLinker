import random
import string

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

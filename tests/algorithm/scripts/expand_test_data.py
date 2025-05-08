import copy
import random
import re
import string

BASE_TEST_FILE = "../data/nbs_test.csv"
EXPANDED_OUTPUT_FILE = "../data/expanded_nbs_test.csv"

ALGORITHM_RELEVANT_COLUMNS = [
    "BIRTHDATE",
    "FIRST",
    "LAST",
    "SUFFIX",
    "GENDER",
    "ADDRESS",
    "CITY",
    "ZIP",
    "SSN"
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
        if test_case[field] == None or test_case[field] == "":
            missing_fields.append(field)
    return missing_fields


def apply_field_scrambling(
        test_case: dict[str, str],
        fields_to_scramble: list[str]
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
                    base_value = base_value[:e[1]] + e[2] + base_value[e[1]:]
                # Add to the end, just concatenate
                else:
                    base_value += e[2]
            
            # Deleting is just splicing out the character
            elif e[0] == "delete":
                if e[1] == len(base_value) - 1:
                    base_value = base_value[:len(base_value) - 1]
                else:
                    base_value = base_value[:e[1]] + base_value[e[1] + 1:]

            # Python strings are immutable and can't be assigned, so just
            # reconstruct a new string with the letters manually inserted
            else:
                left_char = base_value[e[1]]
                right_char = base_value[e[1] + 1]
                base_value = base_value[:e[1]] + right_char + left_char + base_value[e[1] + 2:]
        test_case[f] = base_value
    
    return test_case


# Start by reading in the file
test_cases = []
with open(BASE_TEST_FILE, 'r') as fp:
    test_cases = fp.readlines()

# Now, let's do a bit of formatting and parsing:
# Each case will be a dict mapping a formatted value to the
# appropriate header
headers = [h.strip() for h in test_cases[0].split(",")]
test_cases = test_cases[1:]
# Some field values are double-quoted strings which themselves contain commas
# Can't use regular str.split, have to use regex
test_cases = [
    [x.strip() for x in re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', tc)] for tc in test_cases
]
test_cases = [dict(zip(headers, tc)) for tc in test_cases]

# We'll run a duplication and scrambling procedure on each of the 
# cases in the given file
cases_to_write = []
for tc in test_cases:
    # Start by adding the base case to our output list
    cases_to_write.append(tc)
    missing_fields_in_case = identify_missing_fields(tc)
    acceptable_fields_to_drop = [
        f for f in ALGORITHM_RELEVANT_COLUMNS if f not in missing_fields_in_case
    ]

    # Generate the duplicates for this case
    for _ in range(random.randint(MIN_DUPLICATE_CASES, MAX_DUPLICATE_CASES)):
        dupe = copy.deepcopy(tc)

        # Determine if this duplicate will be subject to field dropout
        fields_to_drop = []
        if random.random() < CHANCE_TO_DROP_FIELDS:
            # Randomly determine fields to drop from this duplicate, only dropping
            # fields that weren't already dropped in the original test case
            fields_to_drop = random.sample(
                acceptable_fields_to_drop,
                random.randint(MIN_FIELDS_TO_DROP, MAX_FIELDS_TO_DROP)
            )
            for f in fields_to_drop:
                dupe[f] = ""

        # Determine if this duplicate will be subject to field scrambling
        if random.random() < CHANCE_TO_SCRAMBLE:
            # Determine which fields are safe to scramble (can't be missing)
            safe_to_scramble = [
                f for f in acceptable_fields_to_drop if f not in fields_to_drop
            ]
            fields_to_scramble = random.sample(
                safe_to_scramble,
                random.randint(MIN_FIELDS_TO_SCRAMBLE, MAX_FIELDS_TO_SCRAMBLE)
            )
            dupe = apply_field_scrambling(dupe, fields_to_scramble)

        # A freshly baked dupe, add it to the output list
        cases_to_write.append(dupe)
    
# We now have a list of fully processed expanded test cases
# Let's randomize it to mitigate ordering bias, then write it out
random.shuffle(cases_to_write)
with open(EXPANDED_OUTPUT_FILE, 'w') as fp:
    # Start with the headers
    fp.write(",".join(headers) + "\n")

    for write_case in cases_to_write:
        # Format each test case as a comma-separated delineation of fields
        case_string = ""
        for h in headers:
            case_string += write_case[h] + ","
        # One extra dangling comma, get rid of it
        case_string = case_string[:-1] + "\n"
        fp.write(case_string)
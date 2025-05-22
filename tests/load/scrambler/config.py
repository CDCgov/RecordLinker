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

# Range of the number of copies to make of each test case, before
# applying scrambling. Value is chosen randomly within the range.
# Note that the range of how many cases you end up with for each
# starting case is this range + 1, since you have the original case
# plus the duplicates (we want to preserve the original test, too)
MIN_DUPLICATE_CASES = 2
MAX_DUPLICATE_CASES = 10

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

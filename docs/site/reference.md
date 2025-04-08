# Reference

## Algorithm Configuration

The Algorithm configurations are stored in the database and can be managed via the API.
Many of the attributes defined on a configuration are limited to a specific set of values,
which are defined here.

### Features

The `Feature` enum defines the types of attributes that can be used for matching during the
linkage evaluation phase. The following features are supported:

`BIRTHDATE`

:   The patient's birthdate (normalized to `YYYY-MM-DD`). If a birthdate with an ambiguous (i.e. 
given as a two-digit year, rather than as four digits) year is provided, RecordLinker parses the 
birthdate as `19XX` if the given year is after the two-digit year of the current calendar year 
(`47`, for example, would become `1947`), and parses the birthdate as `20XX` otherwise (`08` and
`25` would become `2008` and `2025`, respectively). If a patient's birthdate is given as a date 
in the future, parsing the birthdate will generate an error message and result in a failure.

`SEX`

:   The patient's sex (normalized to `M` or `F`).

`RACE`

:   The patient's race in the format of "AMERICAN_INDIAN", "ASIAN", "BLACK", "HAWAIIAN", "WHITE", "OTHER", "ASKED_UNKNOWN" or "UNKNOWN".

`GIVEN_NAME`

:   The patient's given name, this includes first and middle names.

`FIRST_NAME`

:   The patient's first name.

`LAST_NAME`

:   The patient's last name.

`NAME`

:   The patient's full name. (We recommend only using this field for checking skip values, for feature matching we recommend using `FIRST_NAME` and `LAST_NAME` for best results)

`SUFFIX`

:   The patient's name suffix.

`ADDRESS`

:   The patient's address (street suffixes normalized per [USPS rules](https://pe.usps.com/text/pub28/28apc_002.htm)).

`CITY`

:   The patient's city.

`STATE`

:   The patient's state, normalized to standard USPS two-letter codes.

`ZIP`

:   The patient's 5 digit zip code.

`COUNTY`

:   The patient's county.

`TELECOM`

:   The patient's phone, email, fax, or other contact information.

`PHONE`

:   The patient's phone number normalized to an E164 string, although only national numbers (i.e., no country codes) are used for comparison purposes.

`EMAIL`

:   The patient's email address.

`IDENTIFIER`

:   An identifier for the patient.  Matching on this will check if any identifier value/authority/type combination matches.

`IDENTIFIER:<type>`

:   The patient's specific identifier type. For example, `IDENTIFIER:MR` would be the patient's medical record number.  Unlike `IDENTIFIER`, this will ONLY compare values of a specific type.  Valid type codes can be found on [the R4 FHIR Identifier Type v2 page](http://hl7.org/fhir/R4/v2/0203/index.html).


### Blocking Key Types

The `BlockingKey` enum defines the types of blocking values that are generated from the 
patient data and used during query retrieval. The following blocking key types are supported:

`BIRTHDATE` (ID: **1**)

:   The patient's birthdate in the format `YYYY-MM-DD`.

`SEX` (ID: **3**)

:   The patient's sex in the format of `M` or `F`.

`ZIP` (ID: **4**)

:   The patient's  5 digit zip code.

`FIRST_NAME` (ID: **5**)

:   The first 4 characters of the patient's first name.

`LAST_NAME` (ID: **6**)

:   The first 4 characters of the patient's last name.

`ADDRESS` (ID: **7**)

:   The first 4 characters of the patient's address.

`PHONE` (ID: **8**)

:   The last 4 digits of the patient's phone number (excluding extensions).

`EMAIL` (ID: **9**)

:   The first 4 characters of the patient's email address.

`IDENTIFIER` (ID: **10**)

:  A colon separated string of the last 4 characters of the value and the identifier type.


### Evaluation Functions

These are the functions that can be used to evaluate the matching results as a collection, thus
determining it the incoming payload is a match or not to an existing Patient record.

`func:recordlinker.linking.matchers.rule_probabilistic_match`

:   Determines whether a given set of feature comparisons matches enough to be the
    result of a true patient link instead of just random chance. This is represented
    using previously computed log-odds ratios. A `true_match_threshold` needs to be set
    in the `kwargs` parameter to determine the minimum log-odds ratio that is considered
    a match. Example: `{"kwargs": {"true_match_threshold": 12.5}}`

### Feature Matching Functions

These are the functions that can be used to compare the values of two features to determine
if they are a match or not.

**Note**: When most features are compared, we are doing a 1 to 1 comparison (e.g. "M" == "M").
However, some features have the ability to have multiple values (e.g. `ADDRESS`), thus feature
matching is designed to compare one list of values to another list of values.  For example, an
incoming record could have a ADDRESS of
[{"address": ["123 Main St", "apt 2"], "city": "Springfield", "state": "IL"}] and want to compare
that to an existing Patient with the ADDRESS of
[{"address": ["123 Main Street"], "city": "Springfield", "state": "IL"}, {"address": ["456 Elm St"], "state": "IL"}].
In that case we'd want to evaluate "123 Main St" against both "123 Main Street" and "456 Elm St".

`func:recordlinker.linking.matchers.compare_probabilistic_exact_match`

:   Determines if a Feature Field has the same value in two different patient records. If the two fields agree
    exactly (i.e. are exactly the same), then the function returns the full extent of the log-odds weights for 
    the particular field with which it was called. If the two fields do not exactly agree, the function returns
    0.0. This is useful when performing probabilistic comparisons (which score a possible match's strength by
    accumulating a sum of link weights) on fields for which fuzzy similarity doesn't make sense, such as fields
    defined by an enum (e.g. Sex). Use the kwargs parameter to specify the log-odds ratios based on training.
    Example: `{"kwargs": {"log_odds": {"SEX": 6.8}}}`

`func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match`

:   Similar to the above function, but uses a log-odds ratio to determine if the features are a match 
    probabilistically. This is useful when wanting to more robustly compare features by incorporating
    their predictive power (i.e., the log-odds ratio for a feature represents how powerful of a predictor
    that feature is in determining whether two patient records are a true match, as opposed to a match
    by random chance). Use the kwargs parameter to specify the fuzzy match threshold and log-odds ratio
    based on training. Example: `{"kwargs": {"thresholds": {"FIRST_NAME": 0.8}, "log_odds": {"FIRST_NAME": 6.8}}}`

One important caveat for both of these Feature Functions is how they handle patient
records with missing information in one or more fields.  RecordLinker provides the option 
to match records that are missing some data, e.g., Field X, with other records for which that 
data (Field X) is present. In order to enable this possibility, and to avoid overly penalizing 
records which may be strong matches but simply have data omitted due to collection 
methods, both of these feature functions include a partial log-odds weighting. If one or more 
records being compared is missing data for a field, each of the above functions returns exactly 
half the log-odds weight for the field overall, along with a boolean flag indicating that data was 
missing during comparison.

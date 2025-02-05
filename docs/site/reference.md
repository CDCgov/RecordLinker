# Reference

## Algorithm Configuration

The Algorithm configurations are stored in the database and can be managed via the API.
Many of the attributes defined on a configuration are limited to a specific set of values,
which are defined here.

### Features

The `Feature` enum defines the types of attributes that can be used for matching during the
linkage evaluation phase. The following features are supported:

`BIRTHDATE`

:   The patient's birthdate (normalized to `YYYY-MM-DD`).

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

`SUFFIX`

:   The patient's name suffix.

`ADDRESS`

:   The patient's address.

`CITY`

:   The patient's city.

`STATE`

:   The patient's state.

`ZIP`

:   The patient's 5 digit zip code.

`COUNTY`

:   The patient's county.

`TELECOM`

:   The patient's phone, email, fax, or other contact information.

`PHONE`

:   The patient's phone number (normalized to 10 digits).

`EMAIL`

:   The patient's email address.

`IDENTIFIER`

:   An identifier for the patient.  Matching on this will check if any identifier type/authority/value combination matches.

`IDENTIFIER:<type>`

:   The patient's specific identifier type. For example, `IDENTIFIER:MR` would be the patient's medical record number.  Unlike `IDENTIFIER`, this will ONLY compare values of a specific type.  Valid type codes can be found on [the R4 FHIR Identifier Type v2 page](http://hl7.org/fhir/R4/v2/0203/index.html).


### Blocking Key Types

The `BlockingKey` enum defines the types of blocking values that are generated from the 
patient data and used during query retrieval. The following blocking key types are supported:

`BIRTHDATE` (ID: **1**)

:   The patients birthdate in the format `YYYY-MM-DD`.

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

:   The last 4 digits of the patient's phone number.

`EMAIL` (ID: **9**)

:   The first 4 characters of the patient's email address.

`IDENTIFIER` (ID: **10**)

:  A colon separated string of the identifier type, first 2 characters of the authority and last 4 characters of the value.


### Evaluation Functions

These are the functions that can be used to evaluate the matching results as a collection, thus
determining it the incoming payload is a match or not to an existing Patient record.

`func:recordlinker.linking.matchers.rule_match`

:   Determines whether a given set of feature comparisons represent a 'perfect' match
    (i.e. all features that were compared match in whatever criteria was specified).

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
However, some features have the ability to have multiple values (e.g. `GIVEN_NAME`), thus feature
matching is designed to compare one list of values to another list of values.  For example, an
incoming record could have a GIVEN_NAME of ["John", "Dean"] and we could be comparing them to an
existing Patient with the GIVEN_NAME of ["John", "D"].

`func:recordlinker.linking.matchers.compare_match_any`

:   Determines if any of the features are a direct match.

`func:recordlinker.linking.matchers.compare_match_all`

:   Determines if all of the features are a direct match.

`func:recordlinker.linking.matchers.compare_fuzzy_match`

:   Determines if the features are a fuzzy match based on a string comparison.
    JaroWinkler, Levenshtein and Damerau-Levenshtein are supported, with JaroWinkler as the default.
    Use the `kwargs` parameter to specify the desired algorithm and thresholds.
    Example: `{"kwargs": {"similarity_measure": "levenshtein", "thresholds": {"FIRST_NAME": 0.8}}}`

`func:recordlinker.linking.matchers.compare_probabilistic_fuzzy_match`

:   Similar to the above function, but uses a log-odds ratio to determine if the features are a match 
    probabilistically. This is useful when wanting to more robustly compare features by incorporating
    their predictive power (i.e., the log-odds ratio for a feature represents how powerful of a predictor
    that feature is in determining whether two patient records are a true match, as opposed to a match
    by random chance). Use the kwargs parameter to specify the fuzzy match threshold and log-odds ratio
    based on training. Example: `{"kwargs": {"thresholds": {"FIRST_NAME": 0.8}, "log_odds": {"FIRST_NAME": 6.8}}}`

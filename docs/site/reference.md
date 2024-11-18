# Reference

## Algorithm Configuration

The Algorithm configurations are stored in the database and can be managed via the API.
Many of the attributes defined on a configuration are limited to a specific set of values,
which are defined here.

### Features

The `Feature` enum defines the types of attributes that can be used for matching during the
linkage evaluation phase. The following features are supported:

`BIRTHDATE`

:   The patient's birthdate in the format `YYYY-MM-DD`.

`MRN`

:   The patient's medical record number.

`SSN`

:   The patient's social security number.

`SEX`

:   The patient's sex in the format of `M`, `F`, or `U` for unknown.

`GENDER`

:   The gender the patient identifies with in the format of "FEMALE", "MALE", "NON_BINARY", "ASKED_DECLINED" or "UNKNOWN".

`RACE`

:   The patient's race in the format of "AMERICAN_INDIAN", "ASIAN", "BLACK", "HAWAIIAN", "WHITE", "OTHER", "ASKED_UNKNOWN" or "UNKNOWN".

`FIRST_NAME`

:   The patient's given name, this includes first and middle names.

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

`TELEPHONE`

:   The patient's telephone number.

`DRIVERS_LICENSE`

:   The patient's driver's license number.


### Blocking Key Types

The `BlockingKey` enum defines the types of blocking values that are generated from the 
patient data and used during query retrieval. The following blocking key types are supported:

`BIRTHDATE` (ID: **1**)

:   The patients birthdate in the format `YYYY-MM-DD`.

`MRN` (ID: **2**)

:   The last 4 characters of a patient's medical record number.

`SEX` (ID: **3**)

:   The patient's sex in the format of `M`, `F`, or `U` for unknown.

`ZIP` (ID: **4**)

:   The patient's  5 digit zip code.

`FIRST_NAME` (ID: **5**)

:   The first 4 characters of the patient's first name.

`LAST_NAME` (ID: **6**)

:   The first 4 characters of the patient's last name.

`ADDRESS` (ID: **7**)

:   The first 4 characters of the patient's address.


### Evaluation Functions

These are the functions that can be used to evaluate the matching results as a collection, thus
determining it the incoming payload is a match or not to an existing Patient record.

`func:recordlinker.linking.matchers.eval_perfect_match`

:   Determines whether a given set of feature comparisons represent a 'perfect' match
    (i.e. all features that were compared match in whatever criteria was specified).

`func:recordlinker.linking.matchers.eval_log_odds_cutoff`

:   Determines whether a given set of feature comparisons matches enough to be the
    result of a true patient link instead of just random chance. This is represented
    using previously computed log-odds ratios. A `true_match_threshold` needs to be set
    in the `kwargs` parameter to determine the minimum log-odds ratio that is considered
    a match. Example: `{"kwargs": {"true_match_threshold": 12.5}}`

### Feature Matching Functions

These are the functions that can be used to compare the values of two features to determine
if they are a match or not.

**Note**: When most features are compared, we are doing a 1 to 1 comparison (e.g. "M" == "M").
However, some features have the ability to have multiple values (e.g. `FIRST_NAME`), thus feature
matching is designed to compare one list of values to another list of values.  For example, an
incoming record could have a FIRST_NAME of ["John", "Dean"] and we could be comparing them to an
existing Patient with the FIRST_NAME of ["John", "D"].

`func:recordlinker.linking.matchers.feature_match_any`

:   Determines if any of the features are a direct match.

`func:recordlinker.linking.matchers.feature_match_all`

:   Determines if all of the features are a direct match.

`func:recordlinker.linking.matchers.feature_match_fuzzy_string`

:   Determines if the features are a fuzzy match based on a string comparison.
    JaroWinkler, Levenshtein and Damerau-Levenshtein are supported, with JaroWinkler as the default.
    Use the `kwargs` parameter to specify the desired algorithm and thresholds.
    Example: `{"kwargs": {"similarity_measure": "levenshtein", "thresholds": {"FIRST_NAME": 0.8}}}`

`func:recordlinker.linking.matchers.feature_match_log_odds_fuzzy_compare`

:   Similar to the above function, but uses a log-odds ratio to determine if the features are a match 
    probabilistically. This is useful when wanting to more robustly compare features by incorporating
    their predictive power (i.e., the log-odds ratio for a feature represents how powerful of a predictor
    that feature is in determining whether two patient records are a true match, as opposed to a match
    by random chance). Use the kwargs parameter to specify the fuzzy match threshold and log-odds ratio
    based on training. Example: `{"kwargs": {"thresholds": {"FIRST_NAME": 0.8}, "log_odds": {"FIRST_NAME": 6.8}}}`

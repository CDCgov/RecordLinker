# Reference

## API Documentation

The application uses the [OpenAPI specification](https://www.openapis.org/what-is-openapi) to document the API
endpoints and their expected inputs and outputs.  These docs are available in three different formats when
running the application, the first two for human consumption and the last for machines.

- **Swagger UI**: The [Swagger UI](https://swagger.io/tools/swagger-ui/) format of the docs can be accessed at `/docs`.
- **ReDoc**: The [ReDoc](https://github.com/Redocly/redoc) format of the docs can be accessed at `/redoc`.
- **OpenAPI JSON**: The raw JSON format of the docs can be accessed at `/openapi.json`.

The **ReDoc** format of the [API documentation](api-docs.html) has been built and served with these docs for convenience.


## Algorithm Configuration

The Algorithm configurations are stored in the database and can be managed via the API.
Many of the attributes defined on a configuration are limited to a specific set of values,
which are defined here.

### Features

The `Feature` enum defines the types of attributes that can be used for matching during the
linkage evaluation phase. The following features are supported:

`BIRTHDATE`

:   The patient's birthdate (normalized to `YYYY-MM-DD`).

`MRN`

:   The patient's medical record number.

`SSN`

:   The patient's social security number.

`SEX`

:   The patient's sex (normalized to `M`, `F`, or `U` for unknown).

`GENDER`

:   The gender the patient identifies with in the format of "FEMALE", "MALE", "NON_BINARY", "ASKED_DECLINED" or "UNKNOWN".

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

`PHONE` (ID: **8**)

:   The last 4 digits of the patient's phone number.

`EMAIL` (ID: **9**)

:   The first 4 characters of the patient's email address.


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


### Initial Algorithm Configurations

By default (this can be overridden via an environment variable, see the [Configuration](configuration.md)
guide for more info), the application is configured to be initialized with two starting algorithms;
dibbs-basic and dibbs-enhanced.  The intention of these two configurations are as follows:

`dibbs-basic`

:   The DIBBs Default Algorithm. Based on field experimentation and statistical analysis, this
    deterministic two-pass algorithm combines geographical and personal information to maximize
    linkage quality while minimizing false positives.

`dibbs-enhanced`

:   The DIBBs Log-Odds Algorithm. This optional algorithm uses statistical correction to adjust
    the links between incoming records and previously processed patients (it does so by taking
    advantage of the fact that some fields are more informative than others—e.g., two records
    matching on MRN is stronger evidence that they should be linked than if the records matched on
    zip code). It can be used if additional granularity in matching links is desired. However, while
    the DIBBs Log-Odds Algorithm can create higher-quality links, it is dependent on statistical
    updating and pre-calculated population analysis, which requires some work on the part of the
    user. This is useful for cases where additional precision or stronger matching criteria are
    required.


:   A basic configuration that uses the `BIRTHDATE` and `LAST_NAME` features to determine if a match
    is present.  The `BIRTHDATE` feature is compared using a direct match, while the `LAST_NAME` feature
    is compared using a fuzzy match with a JaroWinkler similarity measure and a threshold of 0.8.

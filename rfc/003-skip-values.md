# RFC: Skip Values

- **Status**: Draft
- **Author(s)**: @ericbuckley
- **Creation Date**: 2025-02-13
- **Last Updated**: 2025-02-14
- **RFC ID**: RFC-003

---

## Summary

There are instances where placeholder values are used in fields to indicate missing data.
In such cases, comparing two placeholder fields is inaccurate, as the presence of missing
data in both documents does not imply they belong to the same individual. This RFC
proposes a system that allows users to specify conditions under which these values should
be excluded from comparisons.

## Motivation

Healthcare organizations often encounter incomplete or missing data and commonly use
placeholder values to indicate this, such as "Unknown" or "Not Specified." In some cases,
placeholders are field-specific, like using "John Doe" or "Jane Doe" for missing patient
names. Comparing two records with the placeholder name "John Doe" does not imply they
belong to the same individual, as the value is a stand-in rather than an actual data point.
An effective record linkage system must account for this and avoid inflating match scores
due to placeholder values. Additionally, since placeholder values can vary across
organizations, the system should offer flexibility for users to define conditions for
excluding these values during comparisons, while also providing a sensible default set of
values for common scenarios.

## Prior Art

A study from the
[Journal of American Medical Informatics Association (JAMIA)](https://academic.oup.com/jamia/article/31/11/2651/7762307)
found that using placeholder values in healthcare data can lead to incorrect patient
matching and using a system with data pre-processing capabilities can help mitigate this issue.
> Linkability measures not only guide the selection of data pre-processing methods such as data cleansing and normalization, but also inform selection or configuration of matching algorithms, all aimed at improving the quality of RL outcomes. For example, LVs exhibiting low missingness (high completeness) generally support more accurate linkage results. However, high completeness may be misleading due to “placeholder” or “default” values (eg, 999-99-9999 for social security number [SSN]), a phenomenon called disguised missingness.

The [University of Waterloo](https://uwaterloo.ca/networks-lab/blog/pre-processing-recordlinkage)
hypothesized that data pre-processing is a crucial step into making data more suitable for
record linkage tasks.

A study from the [NIH](https://pmc.ncbi.nlm.nih.gov/articles/PMC10448229/) agreed that data
quality and completeness affect the ability to make correct linkages.
> However, not all the information entered is valid or is of good quality, for example, placeholder values such as “baby of”, and “unknown”, are observed in the first name field.

## Proposal

This proposal aims to enhance the Record Linker Algorithm configuration by introducing a
new `skip_values` section, allowing users to specify conditions under which certain field
values should be excluded from comparisons. This approach is beneficial because:
    - Algorithm configuration is already user-defined, making the addition of a
        `skip_values` section a natural extension.
    - Organizations may need to manage skip conditions over time as their data evolves,
        and this system provides the flexibility to accommodate those changes.

The `skip_values` section will be defined at the algorithm level (not per pass) and will
contain a list of conditions. Each condition will have two elements: `feature` and `value`.
The `feature` specifies the field to which the condition applies, while `value` indicates
the case-insensitive value to skip. A wildcard value `*` can be used for feature to apply
the condition to all fields. Example:

```json
...
"skip_values": [
  {
    "feature": "NAME",
    "value": "John Doe"
  },
  {
    "feature": "IDENTIFIER:SS",
    "value": "999-99-9999"
  },
  {
    "feature": "*",
    "value": "unknown"
  }
]
```

In this example, the algorithm will exclude fields from comparison if they match:
    - `John Doe` in the patient's name
    - `999-99-9999` in the patient's social security number
    - `unknown` in any patient field

### Pre-Processing Details

Fields that match skip conditions will be removed only from the data copy used for
evaluation, not from the original data stored in the MPI. This ensures that users can
modify skip rules over time or re-run the algorithm without risking data loss.

## Alternatives Considered

Two alternatives were considered, but both have significant drawbacks. The first option is
to apply a data normalization step upon receiving the data to remove any placeholder values.
While similar to the proposed approach, the key difference is that the data is permanently
altered, with placeholder values removed before being persisted. This poses a problem if
users later update their skip values, as any removed data would no longer be available in
the MPI for future use.

The second alternative is to apply specific rules during evaluation to determine whether a
value should be used in a comparison or ignored as a placeholder. The main flaw with this
approach is the lack of context. For example, if comparing the `FIRST_NAME` field and the
incoming record has the value "John", this is typically a valid name for comparison.
However, if the `LAST_NAME` is "Doe", it may be recognized as a placeholder. Performing the
cleaning upfront allows for a comprehensive review of all data fields before evaluation,
ensuring that additional context is considered.

## Risks and Drawbacks

The primary drawback of this approach is the added complexity, as it introduces an
additional step to the process. Previously, the core steps for running linkage were:
    1. Data normalization
    2. Blocking
    3. Comparisons (also known as evaluation)
    4. Aggregation and prediction

With the new approach, a "cleaning" step is added between steps 1 and 2. While the
computational overhead of this additional step is minimal, the increased complexity is a
concern. Each added step makes the system more challenging to evolve and harder for both
users and developers to understand.

## Implementation Plan

For the purposes of this RFC, we will not be overly prescriptive about the implementation
details. However, the work can be broadly divided into three tasks:
    1. A new `NAME` feature will be created, that will allow us to specify skip conditions
        for the entirety of the name specified. (This likely won't be used for evaluation,
        as its still preferable to compare the first and last names separately, but users
        will have that option)
    2. Modify the existing Algorithm schema to include the new `skip_values`attribute,
        along with parsing these values and storing the specified conditions.
    3. Implement a new cleaning step that takes the incoming data payload and a list of skip
        conditions, then returns a copy of the data payload with placeholder values removed.
        This cleaned copy will be used for blocking, evaluation, and aggregation, while the
        original incoming payload will be retained for persistence.

## Unresolved Questions

A key question to consider is whether the concept of skip value conditions accounts for all
possible scenarios. Do we need more complex rules that evaluate multiple attributes
simultaneously? For example, should an `ADDRESS` of "123 Main St" be skipped only if the
`ZIP` is also "99999"? While supporting rules of this complexity wouldn't require
significant changes to the specification, it would increase the implementation complexity.
We recommend pursuing this type of **and** logic only if there is a clear and specific need
for it.

---

## Footnotes or References

- [Internal research on common skip values to consider](https://cdc.sharepoint.com/:w:/r/teams/OPHDST-IRD-DIBBs/_layouts/15/Doc.aspx?sourcedoc=%7B543cf7ff-8992-41aa-8595-5b49194b5c3a%7D&action=editnew).

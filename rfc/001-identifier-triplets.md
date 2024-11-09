# RFC: Identifier Triplets

- **Status**: Draft
- **Author(s)**: @ericbuckley
- **Creation Date**: 2024-11-09
- **Last Updated**: 2024-11-09
- **RFC ID**: RFC-001

---

## Summary

There are numerous identifiers that are used across healthcare documents to uniquely identify patients.
Implementing each of these manually is time-consuming, error-prone and can lead to inconsistencies.
This RFC proposes a standard set of identifier triplets that can be used to uniquely identify patients
across healthcare documents and a process for how we can compare them in Record Linker.

## Motivation

NBS currently supports over a dozen different identifiers for patients, while Record Linker only has support
for three (MRN, SSN and Driver's License). This makes it difficult to configure Record Linker to run comparisons
on all fields that customers may want to link on.  Additionally, there differences in how we currently handle
comparisons on MRN, SSN and Driver's License, which can confuse users configuring business rules and lead to
inconsistent results.  Standardizing the way identifiers are compared will make it easier for users to configure
Record Linker and will lead to more consistent results.

## Prior Art

[FHIR currently uses a 6-tuple](https://www.hl7.org/fhir/datatypes.html#Identifier) of identifier use, type,
system, value, period and assigner to uniquely identify patients.  While all of these fields are optional, some
are almost always used in practice (eg value and type).  NBS currently uses a 3-tuple system of type, authority
and value.  Between the two, type and value are directly comparable, while assigner and authority offer similar
functionality.

## Background

Field (aka feature) comparisons happen in two phases of the Record Linker process: blocking and evaluation.
Blocking is the process of quickly reducing the number of existing documents to compare against, so the evaluation
phase can be more efficient.  Evaluation is the process of comparing the remaining documents in detail to determine
if they are the same or different.  Blocking is meant to be fuzzy, as its just for performance, evaluation is meant
for detailed comparisons to really determine if two documents are the same or different.

Blocking has been optimized to join against a separate index table (ie the blocking values table) to quickly reduce
the number of documents to compare against.  This table has 3 main columns to facilitate this: the patient id, the
blocking key and the value.  The blocking key is essentially the field name in which we are comparing against,
however it is not a direct mapping.  For example the `LAST_NAME` blocking field only contains the first 4 chars of
the last name.  The important thing to note is we have one fixed blocking key column (eg `LAST_NAME`, `SEX`,
`IDENTIFIER`) and one variable value column (`Smit`, `M`, `123-45-6789`).

Evaluation, the process of comparing documents in code, has more flexibility in we can create different functions
for comparing different fields.  The general process though has been to compare a list of string values for each
field.  While many fields only have 1 value (eg `SEX`, `RACE`, `BIRTH_DATE`), some fields have multiple values
(eg `ADDRESS`, `FIRST_NAME`, `LAST_NAME`).  Thus it was important to implement the evaluation functions to
accept a list of strings for both the incoming document and the existing document when comparing these fields.
The important thing to note here, is if we are comparing a field like `IDENTIFIER`, we are likely limited to
just comparing 1 string value per identifier listed in a document (we are assuming more than 1 identifier can
be listed in a document).

## Proposal

The proposal is to use a 3-tuple of type, authority and value to specify patient identifiers and evaluate them.

- Input: A list of identifier objects, each with a type, authority and value.
    example: `[{type: 'DL', authority: 'CA', value: 'A123456'}, {type: 'SS', authority: '', value: '123-45-6789'}]`
- Business Rules: Algorithm configuration will accept the `IDENTIFIER` field with a type suffix, to specify
    the type of identifier to compare.
    example: `IDENTIFIER:DL`, `IDENTIFIER:SSN`
- Blocking: The blocking key will be `IDENTIFIER` and values will be inserted for every identifier specified in
    the document using the type and the last four of the value.
    example: `IDENTIFIER:DL:3456`, `IDENTIFIER:SSN:6789`
- Evaluation: The evaluation function will accept a list of identifier strings, containing all 3 parts of the
    tuple, and compare them using the specified evaluation function.
    example: `['DL:CA:A123456', 'SS::123-45-6789']`

### Input

TBD

### Business Rules

TBD

### Blocking

TBD

### Evaluation

TBD

## Alternatives Considered

**(Replace this text)** List any alternative solutions that were considered and explain why they were not chosen. This helps reviewers understand the trade-offs and decision-making process.

## Risks and Drawbacks

**(Replace this text)** Outline any potential risks, drawbacks, or negative implications of implementing this proposal. Consider the impact on users, maintainers, performance, and other factors.

## Implementation Plan

**(Replace this text)** Provide an overview of the steps required to implement the proposal, if it is accepted. Include any necessary code changes, documentation updates, migration plans, etc.

## Unresolved Questions

**(Replace this text)** List any open questions that still need to be addressed. This section can be used to highlight uncertainties and gather feedback from reviewers.

## Future Possibilities

**(Replace this text)** (Optional) Describe any future improvements or extensions that could be considered after implementing this proposal.

---

## Footnotes or References

 **(Replace this text)** Include links to relevant documents, issues, discussions, or additional resources.

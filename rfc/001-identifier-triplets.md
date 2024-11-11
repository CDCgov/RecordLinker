# RFC: Identifier Triplets

- **Status**: Draft
- **Author(s)**: @ericbuckley
- **Creation Date**: 2024-11-09
- **Last Updated**: 2024-11-11
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
    example: `IDENTIFIER:DL`, `IDENTIFIER:SS`
- Blocking: The blocking key will be `IDENTIFIER` and values will be inserted for every identifier specified in
    the document using the type and the last four of the value.
    example: `DL:CA:3456`, `SS::6789`
- Evaluation: The evaluation function will accept a list of identifier strings, containing all 3 parts of the
    tuple, and compare them using the specified evaluation function.
    example: `['DL:CA:A123456', 'SS::123-45-6789']`

### Input

The input to the Record Linker process will be a list of identifier objects, each with a type, authority and value.
The type and value attributes are required, while authority is optional.

```json
{
    "identifiers": [
        {
            "type": "DL",
            "authority": "CA",
            "value": "A123456"
        },
        {
            "type": "SS",
            "authority": "",
            "value": "123-45-6789"
        }
    ]
}
```

The type attribute will be limited to a codes defined by the
[HL7 identifierType code system](https://terminology.hl7.org/6.0.2/CodeSystem-v2-0203.html). This 
includes roughly 100 different types of identifiers that are all coded using a 2-7 character value.
For example, `DL` is the code for Driver's License, `SS` is the code for Social Security Number, `MR`
is the code for Medical Record Number.

The authority attribute will be a free-form string that can be used to specify the issuing authority
of the identifier.  For example, `CA` could be used to specify that the Driver's License was issued
by the state of California.  There is no standard code system for this attribute, so it will be up to
the user to specify a value that makes sense for their data.

The value attribute will be a free-form string that contains the actual value of the identifier.  For
example, `A123456` could be the value of a Driver's License, `123-45-6789` could be the value of a
Social Security Number.


### Business Rules

When specifying a blocking key or evaluation field in an Algorithm configuration, identifier matches
can be specified in two different forms.  The first form, which is applicable to blocking keys
and evaluation fields, is to specify `IDENTIFIER` indicating it will match on any like identifier.
The second form, which is **only applicable to evaluation fields**, is to specify `IDENTIFIER:<type>`
indicating it will match on a specific type of identifier.

```json
{
    "blocking_keys": [
        "IDENTIFIER",
        "BIRTH_DATE",
    ],
    "evaluators": {
        "IDENTIFIER": "func:recordlinker.linking.matchers.feature_match_exact",
    }
}
```

```json
{
    "blocking_keys": [
        "IDENTIFIER",
        "BIRTH_DATE",
    ],
    "evaluators": {
        "IDENTIFIER:SS": "func:recordlinker.linking.matchers.feature_match_exact",
    }
}
```

### Blocking

Blocking keys are an important part of the linkage process, but only from a performance perspective.
We use these values to efficiently index the documents, and pull out a subset of documents to compare
in detail. For them to work efficiently, we have some limitations to the size of the values we can
store in the blocking table.  Currently, that is limited to 20 characters which is a bit arbitrary,
but the idea is to keep the values small so we can index them efficiently.  If we keep that limit, we
need to use identifier values that are guaranteed to be less than that limit.

Previous research has shown that the last **4 characters of an identifier value** are often the most
unique and can be used to block on.  However, we should likely also include elements of the type and
authority, if we want to provide some assurance that we are not blocking on a different identifier
all together. For that, we recommend storing the **entire type** (which is limited to 7 characters)
and the **first 2 characters of the authority** (which is free-form).

| patient_id | blocking_key | value      |
|------------|--------------|------------|
| 1          | IDENTIFIER   | DL:CA:3456 |
| 1          | IDENTIFIER   | SS::6789   |

### Evaluation

As indicated in the business rules section, evaluation on identifiers can happen in two ways. The
first way is to evaluate on any identifier, meaning that the evaluation step will result in a
match if any two identifiers between the documents are a match.  The second way is to evaluate on
a specific type of identifier, meaning that the evaluation step will result in a match if the 
specified type of identifier between the documents is a match.

The evaluation functions will be comparing all 3 parts of the identifier tuple (type, authority,
value) when determining if two identifiers are a match.  The difference is just between what types
of identifiers are we going to compare.

```python

if feature == 'IDENTIFIER':
    assert values == ['DL:CA:A123456', 'SS::123-45-6789']
if feature == 'IDENTIFIER:SS':
    assert values == ['SS::123-45-6789']
```

## Alternatives Considered

The main alternative to a generic identifier triplet is to continue creating specific fields (eg 
`MRN`, `SSN`, `drivers_license`) for each identifier type.  This would require more configuration
and would not be as flexible as the proposed solution. However, this does allow for customization's
when blocking or evaluating on specific identifier types.  For example, we know that SSN will never
require an authority, so we can make a slight reduction in the blocking value size knowing that is
never required.  In the case of Driver's License, we know that the authority will always be a state,
so we could implement custom normalization logic attempting to standardize the state values (eg `CA`
vs `California`).  This is more work long-term, and likely more confusing for users as each identifier
field has slightly different behavior, but does allow for maximum flexibility.

## Risks and Drawbacks

- Variations in authority values could lead to false negatives in comparisons (eg `CA` vs `California`).
- Variations in value formats could lead to false negatives in comparisons (eg `123-45-6789` vs `123456789`).
- Blocking values can't be specified per type, so if we want to block on identifiers we need to block on all.

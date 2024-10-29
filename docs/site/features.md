# Features

Features are the PII attributes in which the RecordLinker service compares when
making a record linkage decision. In order to support additional features, the
following steps should be taken:

### Add the New Feature to the `Feature` Class
- In [src/recordlinker/schemas/pii.py](https://github.com/CDCgov/RecordLinker/blob/main/src/recordlinker/schemas/pii.py), add the new feature to the [Feature](https://github.com/CDCgov/RecordLinker/blob/main/src/recordlinker/schemas/pii.py) enum class.

### Update the `PIIRecord` Schema
- In the same file, modify the [PIIRecord](https://github.com/CDCgov/RecordLinker/blob/main/src/recordlinker/schemas/pii.py) class to include the new feature as a field.
- If the feature requires predefined values, create an enum to represent those values.

### Modify the `PIIRecord.feature_iter` Method
- Update the [PIIRecord.feature_iter](https://github.com/CDCgov/RecordLinker/blob/main/src/recordlinker/schemas/pii.py) method to return the value of the new feature when it's used for comparison.

### Extract the FHIR Field in `fhir_record_to_pii_record`
- In [src/recordlinker/linking/link.py](https://github.com/CDCgov/RecordLinker/blob/main/src/recordlinker/linking/link.py), update the [fhir_record_to_pii_record](https://github.com/CDCgov/RecordLinker/blob/main/src/recordlinker/linking/link.py) function to map the relevant FHIR field to the new feature in [PIIRecord](https://github.com/CDCgov/RecordLinker/blob/main/src/recordlinker/schemas/pii.py).

### Update the Tests
- Add or modify unit tests to verify that the new feature is properly extracted, mapped, and compared. 

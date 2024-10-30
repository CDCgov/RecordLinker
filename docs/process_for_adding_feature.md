# Adding a New Feature

### Add the New Feature to the `Feature` Class
- In [src/recordlinker/schemas/pii.py](https://github.com/CDCgov/RecordLinker/blob/a672d2b6409cbd1a08f729d94fba5692f57f6fc6/src/recordlinker/schemas/pii.py), add the new feature to the [Feature](https://github.com/CDCgov/RecordLinker/blob/a672d2b6409cbd1a08f729d94fba5692f57f6fc6/src/recordlinker/schemas/pii.py#L12C7-L12C14) enum class.

### Update the `PIIRecord` Schema
- In the same file, modify the [PIIRecord](https://github.com/CDCgov/RecordLinker/blob/c85f555e5da91d54eb8c51e3bdf0789d1e204b2f/src/recordlinker/schemas/pii.py#L97) class to include the new feature as a field.
- If the feature requires predefined values, create an enum to represent those values.

### Modify the `PIIRecord.feature_iter` Method
- Update the [PIIRecord.feature_iter](https://github.com/CDCgov/RecordLinker/blob/a672d2b6409cbd1a08f729d94fba5692f57f6fc6/src/recordlinker/schemas/pii.py#L246) method to return the value of the new feature when it's used for comparison.

### Extract the FHIR Field in `fhir_record_to_pii_record`
- In [src/recordlinker/linking/link.py](https://github.com/CDCgov/RecordLinker/blob/e8a64407b6e8564595cad6380d5291e9f5c959e3/src/recordlinker/parsers/fhir.py), update the [fhir_record_to_pii_record](https://github.com/CDCgov/RecordLinker/blob/e8a64407b6e8564595cad6380d5291e9f5c959e3/src/recordlinker/parsers/fhir.py#L12) function to map the relevant FHIR field to the new feature in [PIIRecord](https://github.com/CDCgov/RecordLinker/blob/e8a64407b6e8564595cad6380d5291e9f5c959e3/src/recordlinker/schemas/pii.py#L141).

### Update the Tests
- Add or modify unit tests to verify that the new feature is properly extracted, mapped, and compared. 
# Developer Guide

## Release Process

This document outlines our release process, from the automatic creation of draft releases to the tagging and publishing of final releases.

### 1. Draft Release Creation

Whenever pull requests are merged into the `main` branch, a new **draft release** is automatically generated. This draft is based on the differences between the last official release and the current state of the `main` branch.

- Only **one draft release** is maintained at any given time, tracking all upcoming changes.
- As more pull requests are merged, the existing draft release is updated with the new changes. This ensures that the draft release always reflects the latest features, fixes, and updates heading to production.

### 2. Release Tagging and Publishing

To publish a release, a developer with the appropriate permissions pushes a release tag. The tag format is structured as follows:

`vYY.FF.HH`

- **YY**: Two-digit calendar year (e.g., `24` for the year 2024).
- **FF**: Number of the **planned release** for the calendar year. Increment this with each planned feature release.
- **HH**: Number of **unplanned releases** (hotfixes) since the last planned feature release. This resets after each feature release.

#### Examples:

- `v24.3.0`: This tag represents the third planned release of the year 2024.
- `v24.1.1`: This tag represents the first unplanned release of the year 2024, after the first planned release.

#### Publishing Process:
- When a developer pushes a release tag, the process automatically publishes the existing draft release with the corresponding tag.
- **Only users with the `maintain` or `admin` role** can push version tags, ensuring controlled and authorized release management.

### 3. Release Notes

Our release descriptions are **automatically generated** by GitHub based on the merged pull requests and commit history.

- The format and content of these release notes can be customized by editing the `.github/release.yml` file.
- For more information on customizing release notes, refer to [GitHub’s documentation on automatically generated release notes](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes).


## Adding Features

Features are the PII attributes in which the RecordLinker service compares when
making a record linkage decision. In order to support additional features, the
following steps should be taken:

### Add the New Feature to the `Feature` Class
- In [src/recordlinker/schemas/pii.py](https://github.com/CDCgov/RecordLinker/blob/a672d2b6409cbd1a08f729d94fba5692f57f6fc6/src/recordlinker/schemas/pii.py), add the new feature to the [Feature](https://github.com/CDCgov/RecordLinker/blob/a672d2b6409cbd1a08f729d94fba5692f57f6fc6/src/recordlinker/schemas/pii.py#L12C7-L12C14) enum class.

### Update the `PIIRecord` Schema
- In the same file, modify the [PIIRecord](https://github.com/CDCgov/RecordLinker/blob/c85f555e5da91d54eb8c51e3bdf0789d1e204b2f/src/recordlinker/schemas/pii.py#L97) class to include the new feature as a field.
- If the feature requires predefined values, create an enum to represent those values.

### Modify the `PIIRecord.feature_iter` Method
- Update the [PIIRecord.feature_iter](https://github.com/CDCgov/RecordLinker/blob/a672d2b6409cbd1a08f729d94fba5692f57f6fc6/src/recordlinker/schemas/pii.py#L246) method to return the value of the new feature when it's used for comparison.

### Modify the `linking.clean.clean` Function
- Update the `recordlinker.linking.clean.clean` function to process and remove any data
that matches the new feature.

### Extract the FHIR Field in `fhir_record_to_pii_record`
- In [src/recordlinker/linking/link.py](https://github.com/CDCgov/RecordLinker/blob/e8a64407b6e8564595cad6380d5291e9f5c959e3/src/recordlinker/parsers/fhir.py), update the [fhir_record_to_pii_record](https://github.com/CDCgov/RecordLinker/blob/e8a64407b6e8564595cad6380d5291e9f5c959e3/src/recordlinker/parsers/fhir.py#L12) function to map the relevant FHIR field to the new feature in [PIIRecord](https://github.com/CDCgov/RecordLinker/blob/e8a64407b6e8564595cad6380d5291e9f5c959e3/src/recordlinker/schemas/pii.py#L141).

### Update the Tests
- Add or modify unit tests to verify that the new feature is properly extracted, mapped, and compared. 

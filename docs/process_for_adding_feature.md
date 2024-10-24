# Process for Adding New Feature

Add the New Feature to the Feature Enum
- Open src.recordlinker.schemas.pii.py and add the new feature to the Feature enum class.

Update the PIIRecord Schema
- In the same file, modify the PIIRecord class to include the new feature as a field.
- If the feature requires predefined values, create an enum to represent those values.

Modify the feature_iter Method
- Inside the PIIRecord class, update the feature_iter method to return the value of the new feature when it's used for comparison.

Extract the FHIR Field in fhir_record_to_pii_record
- Go to src.recordlinker.linking.link.py and update the fhir_record_to_pii_record function to map the relevant FHIR field to the new feature in PIIRecord.

Update the Tests
- Add or modify unit tests to verify that the new feature is properly extracted, mapped, and compared. 
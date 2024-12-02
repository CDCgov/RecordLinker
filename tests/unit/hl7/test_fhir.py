"""
unit.parsers.test_fhir.py
~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the unit tests for the recordlinker.parsers.fhir module
"""

import copy

from conftest import load_test_json_asset

from recordlinker.hl7 import fhir


def test_fhir_record_to_pii_record():
    fhir_record = {
        "resourceType": "Patient",
        "id": "f6a16ff7-4a31-11eb-be7b-8344edc8f36b",
        "identifier": [
            {
                "value": "1234567890",
                "type": {
                    "coding": [
                        {
                            "code": "MR",
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "display": "Medical record number",
                        }
                    ]
                },
            },
            {
                "system": "http://hl7.org/fhir/sid/us-ssn",
                "value": "111223333",
                "type": {
                    "coding": [
                        {"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "SS"}
                    ]
                },
            },
            {
                "use": "official",
                "type": {
                    "text": "Driver's License",
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "DL",
                            "display": "Driver's License",
                        }
                    ],
                },
                "system": "urn:oid:2.16.840.1.113883.3.19.3.1.8",
                "value": "D1234567",
                "assigner": {
                    "display": "State DMV",
                    "identifier": {"system": "urn:oid:2.16.840.1.113883.19.3.1.1", "value": "CA"},
                },
            },
        ],
        "name": [{"family": "Shepard", "given": ["John"], "use": "official"}],
        "birthDate": "2053-11-07",
        "gender": "male",
        "address": [
            {
                "line": ["1234 Silversun Strip"],
                "buildingNumber": "1234",
                "city": "Boston",
                "state": "Massachusetts",
                "postalCode": "99999",
                "district": "county",
                "use": "home",
            }
        ],
        "telecom": [{"use": "home", "system": "phone", "value": "123-456-7890"}],
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/individual-genderIdentity",
                "extension": [
                    {
                        "url": "value",
                        "valueCodeableConcept": {
                            "coding": [
                                {
                                    "system": "http://snomed.info/sct",
                                    "code": "446141000124107",
                                    "display": "Identifies as female gender (finding)",
                                }
                            ]
                        },
                    }
                ],
            },
            {
                "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
                "extension": [
                    {
                        "url": "ombCategory",
                        "valueCoding": {
                            "system": "urn:oid:2.16.840.1.113883.6.238",
                            "code": "2106-3",
                            "display": "White",
                        },
                    }
                ],
            },
        ],
    }

    pii_record = fhir.fhir_record_to_pii_record(fhir_record)

    assert pii_record.external_id == "f6a16ff7-4a31-11eb-be7b-8344edc8f36b"
    assert pii_record.name[0].family == "Shepard"
    assert pii_record.name[0].given == ["John"]
    assert str(pii_record.birth_date) == "2053-11-07"
    assert str(pii_record.sex) == "M"
    assert pii_record.address[0].line == ["1234 Silversun Strip"]
    assert pii_record.address[0].city == "Boston"
    assert pii_record.address[0].state == "Massachusetts"
    assert pii_record.address[0].postal_code == "99999"
    assert pii_record.address[0].county == "county"
    assert pii_record.telecom[0].value == "123-456-7890"
    assert pii_record.telecom[0].system == "phone"
    assert str(pii_record.race) == "WHITE"
    assert str(pii_record.gender) == "FEMALE"

    # identifiers
    assert pii_record.identifiers[0].value == "1234567890"
    assert str(pii_record.identifiers[0].type) == "MR"
    assert pii_record.identifiers[0].authority == ""

    assert pii_record.identifiers[1].value == "111-22-3333"
    assert str(pii_record.identifiers[1].type) == "SS"
    assert pii_record.identifiers[1].authority == ""

    assert pii_record.identifiers[2].value == "D1234567"
    assert str(pii_record.identifiers[2].type) == "DL"
    assert pii_record.identifiers[2].authority == "CA"


def test_add_person_resource():
    bundle = load_test_json_asset("patient_bundle.json")
    raw_bundle = copy.deepcopy(bundle)
    patient_id = "TEST_PATIENT_ID"
    person_id = "TEST_PERSON_ID"

    returned_bundle = fhir.add_person_resource(
        person_id=person_id, patient_id=patient_id, bundle=raw_bundle
    )

    # Assert returned_bundle has added element in "entry"
    assert len(returned_bundle.get("entry")) == len(bundle.get("entry")) + 1

    # Assert the added element is the person_resource bundle
    assert returned_bundle.get("entry")[-1].get("resource").get("resourceType") == "Person"
    assert returned_bundle.get("entry")[-1].get("request").get("url") == "Person/TEST_PERSON_ID"

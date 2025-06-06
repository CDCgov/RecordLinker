"""
recordlinker.hl7.fhir
~~~~~~~~~~~~~~~~~~~~~~~~~

This module is used to handle fhir parsing
"""

import typing

import pydantic

from recordlinker import schemas


def get_first_patient_resource(bundle: dict) -> dict:
    """
    Get the first patient resource from a FHIR bundle
    """
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Patient":
            return resource
    return {}


def fhir_record_to_pii_record(fhir_record: dict) -> schemas.PIIRecord:
    """
    Parse the FHIR record into a PIIRecord object
    """
    val = {
        "external_id": fhir_record.get("id"),
        "name": fhir_record.get("name", []),
        "birthDate": fhir_record.get("birthDate"),
        "sex": fhir_record.get("gender"),
        "address": fhir_record.get("address", []),
        "race": [],
        "telecom": fhir_record.get("telecom", []),
        "identifiers": [],
    }
    for identifier in fhir_record.get("identifier", []):
        for code in identifier.get("type", {}).get("coding", []):
            val["identifiers"].append(
                {
                    "value": identifier.get("value"),
                    "type": code.get("code"),
                    "authority": identifier.get("assigner", {})
                    .get("identifier", {})
                    .get("value", ""),
                }
            )
    for address in val["address"]:
        address["county"] = address.get("district", "")
        for extension in address.get("extension", []):
            if extension.get("url") == "http://hl7.org/fhir/StructureDefinition/geolocation":
                for coord in extension.get("extension", []):
                    if coord.get("url") == "latitude":
                        address["latitude"] = coord.get("valueDecimal")
                    elif coord.get("url") == "longitude":
                        address["longitude"] = coord.get("valueDecimal")
    for extension in fhir_record.get("extension", []):
        if extension.get("url") == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race":
            for ext in extension.get("extension", []):
                if ext.get("url") == "ombCategory":
                    val["race"].append(ext.get("valueCoding", {}).get("display"))

    return schemas.PIIRecord(**val)


def add_person_resource(
    person_id: str,
    patient_id: typing.Optional[str] = "",
    bundle: dict = pydantic.Field(description="A FHIR bundle"),
) -> dict:
    """
    Adds a simplified person resource to a bundle if the patient resource in the bundle
    matches an existing record in the Master Patient Index. Returns the bundle with
    the newly added person resource.

    :param person_id: _description_
    :param patient_id: _description_
    :param bundle: _description_, defaults to Field(description="A FHIR bundle")
    :return: _description_
    """
    person_resource = {
        "fullUrl": f"urn:uuid:{person_id}",
        "resource": {
            "resourceType": "Person",
            "id": f"{person_id}",
            "link": [{"target": {"reference": f"Patient/{patient_id}"}}],
        },
        "request": {
            "method": "PUT",
            "url": f"Person/{person_id}",
        },
    }
    bundle.get("entry", []).append(person_resource)
    return bundle

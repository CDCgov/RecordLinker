import json


def dict_to_pii(record_data) -> dict | None:
    # convert row to a pii_record
    pii_record = {
        "external_id": record_data.get('ID', None),
        "birth_date": record_data.get("BIRTHDATE", None),
        "sex": record_data.get("GENDER", None),
        "address": [
            {
                "line": [record_data.get("ADDRESS", None)],
                "city": record_data.get("CITY", None),
                "state": record_data.get("STATE", None),
                "county": record_data.get("COUNTY", None),
                "postal_code": str(record_data.get("ZIP", ""))
            }
        ],
        "name": [
            {
                "given": [record_data.get("FIRST", None)],
                "family": record_data.get("LAST", None),
                "suffix": [record_data.get("SUFFIX", None)]
            }
        ],
        "ssn": record_data.get("SSN", None),
        "race": record_data.get("RACE", None)
    }

    return pii_record


def load_json(file_path: str) -> dict | None:
    """
    Load JSON data from a file.
    """
    with open(file_path, "rb") as fobj:
        try:
            content = json.load(fobj)
            return content
        except json.JSONDecodeError as exc:
            print(f"Error loading JSON file: {exc}")
            return None
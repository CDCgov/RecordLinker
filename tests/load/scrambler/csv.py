def csv_get_field(field: str, data: dict) -> str | None:
    """
    Get the value of a field from a CSV object.
    """
    try:
        value = data.get(field)
        return value
    except KeyError:
        return None


def csv_set_field(field: str, data: dict, value: str) -> None:
    """
    Set the value of a field in a CSV row dictionary.
    """
    data[field] = value

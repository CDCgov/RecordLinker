import unicodedata

import phonenumbers


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison by removing non-alphanumeric characters, converting
    to lowercase, and removing all whitespace (trailing, leading, and internal).
    """
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("ASCII")

    return "".join(c.lower() for c in text if c.isalnum())


def normalize_phone_number(phone_number: str) -> str:
    """
    Normalize phone number into phonenumbers.National format.
    """

    try:
        # Attempt to parse with country code
        if phone_number.startswith("+"):
            parsed_number = phonenumbers.parse(phone_number)
        else:
            # Default to US if no country code is provided
            parsed_number = phonenumbers.parse(phone_number, "US")
        # Return the national phone number only
        return str(parsed_number.national_number)

    except phonenumbers.NumberParseException:
        # If parsing fails, return the original phone number
        return phone_number

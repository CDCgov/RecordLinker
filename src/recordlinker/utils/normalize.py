import unicodedata


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison by removing non-alphanumeric characters, converting
    to lowercase, and removing all whitespace (trailing, leading, and internal).
    """
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("ASCII")

    return "".join(c.lower() for c in text if c.isalnum())

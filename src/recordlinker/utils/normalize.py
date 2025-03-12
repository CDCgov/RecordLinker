import unicodedata


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison by removing non-alphanumeric characters, converting
    to lowercase, and removing all whitespace (trailing, leading, and internal).
    """
    text = "".join(
        c for c in unicodedata.normalize("NFKD", text) if unicodedata.category(c) != "Mn"
    )

    return "".join(c.lower() for c in text if c.isalnum())

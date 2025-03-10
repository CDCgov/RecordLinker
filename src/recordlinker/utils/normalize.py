import re
import unicodedata


def normalize_strings(text: str) -> str:
    """
    Normalize text by removing non-alphanumeric characters and converting to lowercase.
    """
    text = "".join(
        c for c in unicodedata.normalize("NFKD", text) if unicodedata.category(c) != "Mn"
    )
    text = re.sub(r"[^a-zA-Z0-9]", "", text)
    return text.lower()

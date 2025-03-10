import re
import unicodedata


def normalize_text(text: str) -> str:
    """
    Normalize text by removing non-alphanumeric characters, converting to lowercase,
    and removing all whitespace (trailing, leading, and internal).
    """
    text = "".join(
        c for c in unicodedata.normalize("NFKD", text) if unicodedata.category(c) != "Mn"
    )
    text = re.sub(r"[^a-zA-Z0-9]", "", text)
    return text.lower()

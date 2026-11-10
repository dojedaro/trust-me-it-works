import unicodedata


def decompose(text: str) -> str:
    return unicodedata.normalize("NFD", text)

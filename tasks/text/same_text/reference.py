import unicodedata


def _key(s: str) -> str:
    return unicodedata.normalize("NFD", unicodedata.normalize("NFD", s).casefold())


def same_text(a: str, b: str) -> bool:
    return _key(a) == _key(b)

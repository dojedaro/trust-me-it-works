import unicodedata


def matches_initials(query: str, word: str) -> bool:
    if len(query) > len(word):
        return False
    for q, w in zip(query, word):
        if q != w and unicodedata.normalize("NFD", w)[0] != q:
            return False
    return True

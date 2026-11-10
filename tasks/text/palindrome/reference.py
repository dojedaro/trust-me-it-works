import unicodedata


def is_palindrome(text: str) -> bool:
    decomposed = unicodedata.normalize("NFD", text.casefold())
    chars = [c for c in decomposed if not unicodedata.combining(c) and c.isalnum()]
    return chars == chars[::-1]

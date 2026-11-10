def is_palindrome(text: str) -> bool:
    chars = [c for c in text.lower() if c.isalnum()]
    return chars == chars[::-1]

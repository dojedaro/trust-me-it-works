def display_width(text: str) -> int:
    return sum(2 if "\uac00" <= ch <= "\ud7a3" else 1 for ch in text)

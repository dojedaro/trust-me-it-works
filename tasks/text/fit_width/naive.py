def fit(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"

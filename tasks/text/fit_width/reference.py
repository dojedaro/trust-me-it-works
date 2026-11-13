import unicodedata


def _width(ch: str) -> int:
    if unicodedata.category(ch) in ("Mn", "Me", "Cf"):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def _clusters(text: str) -> list[str]:
    out: list[str] = []
    for ch in text:
        if out and _width(ch) == 0:
            out[-1] += ch
        else:
            out.append(ch)
    return out


def fit(text: str, width: int) -> str:
    if sum(_width(c) for c in text) <= width:
        return text
    kept, used = "", 0
    for cluster in _clusters(text):
        w = sum(_width(c) for c in cluster)
        if used + w + 1 > width:
            break
        kept += cluster
        used += w
    return kept + "…"

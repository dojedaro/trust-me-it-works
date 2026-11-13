import re

_PATTERN = re.compile(r"P(?:(\d+)W)?(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?")


def parse_duration(text: str) -> float:
    m = _PATTERN.fullmatch(text)
    if not m:
        raise ValueError(text)
    w, d, h, mi, s = (float(x) if x else 0.0 for x in m.groups())
    return w * 604800 + d * 86400 + h * 3600 + mi * 60 + s

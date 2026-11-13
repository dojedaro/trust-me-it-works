import re

_NUM = r"(\d+(?:[.,]\d+)?)"
_WEEKS = re.compile(rf"P{_NUM}W")
_DAYTIME = re.compile(rf"P(?:{_NUM}D)?(?:T(?:{_NUM}H)?(?:{_NUM}M)?(?:{_NUM}S)?)?")
_SECONDS = (86400, 3600, 60, 1)


def parse_duration(text: str) -> float:
    m = _WEEKS.fullmatch(text)
    if m:
        return float(m.group(1).replace(",", ".")) * 7 * 86400
    m = _DAYTIME.fullmatch(text)
    if not m:
        raise ValueError(f"invalid duration: {text!r}")
    parts = m.groups()
    present = [i for i, p in enumerate(parts) if p is not None]
    if not present:
        raise ValueError(f"empty duration: {text!r}")
    if "T" in text and all(p is None for p in parts[1:]):
        raise ValueError(f"T without a time component: {text!r}")
    if any(re.search("[.,]", parts[i]) for i in present[:-1]):
        raise ValueError(f"only the last component may have a fraction: {text!r}")
    return sum(float(parts[i].replace(",", ".")) * _SECONDS[i] for i in present)

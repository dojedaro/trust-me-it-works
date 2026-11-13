def _key(version: str):
    version = version.split("+", 1)[0]
    core, _, pre = version.partition("-")
    major, minor, patch = (int(x) for x in core.split("."))
    return (major, minor, patch), pre.split(".") if pre else []


def _cmp(x, y) -> int:
    return (x > y) - (x < y)


def _cmp_identifier(x: str, y: str) -> int:
    xn, yn = x.isdigit(), y.isdigit()
    if xn and yn:
        return _cmp(int(x), int(y))
    if xn != yn:
        return -1 if xn else 1
    return _cmp(x, y)


def compare_versions(a: str, b: str) -> int:
    (core_a, pre_a), (core_b, pre_b) = _key(a), _key(b)
    if core_a != core_b:
        return _cmp(core_a, core_b)
    if not pre_a or not pre_b:
        return _cmp(not pre_a, not pre_b)
    for x, y in zip(pre_a, pre_b):
        c = _cmp_identifier(x, y)
        if c:
            return c
    return _cmp(len(pre_a), len(pre_b))

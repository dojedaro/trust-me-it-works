DIGITS = "영일이삼사오육칠팔구"


def _group(g: int) -> str:
    out = ""
    for value, unit in ((1000, "천"), (100, "백"), (10, "십"), (1, "")):
        d = g // value % 10
        if d == 0:
            continue
        out += unit if (d == 1 and unit) else DIGITS[d] + unit
    return out


def read_number(n: int) -> str:
    if n == 0:
        return "영"
    eok, rest = divmod(n, 10**8)
    man, ones = divmod(rest, 10**4)
    out = ""
    if eok:
        out += _group(eok) + "억"
    if man:
        out += "만" if man == 1 else _group(man) + "만"
    if ones:
        out += _group(ones)
    return out

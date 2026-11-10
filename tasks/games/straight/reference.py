ORDER = "23456789TJQKA"


def straight_high(ranks: list[str]) -> str | None:
    values = sorted({ORDER.index(r) for r in ranks})
    if len(values) != 5:
        return None
    if values == [0, 1, 2, 3, 12]:
        return "5"
    if values[-1] - values[0] == 4:
        return ORDER[values[-1]]
    return None

ORDER = "23456789TJQKA"


def straight_high(ranks: list[str]) -> str | None:
    values = sorted(ORDER.index(r) for r in ranks)
    for a, b in zip(values, values[1:]):
        if b != a + 1:
            return None
    return ORDER[values[-1]]

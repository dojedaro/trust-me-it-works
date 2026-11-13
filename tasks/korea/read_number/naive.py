DIGITS = "영일이삼사오육칠팔구"
UNITS = ["", "십", "백", "천", "만", "십", "백", "천", "억", "십", "백", "천"]


def read_number(n: int) -> str:
    if n == 0:
        return "영"
    out = ""
    for power, ch in enumerate(reversed(str(n))):
        d = int(ch)
        if d:
            out = DIGITS[d] + UNITS[power] + out
        elif power in (4, 8):
            out = UNITS[power] + out
    return out

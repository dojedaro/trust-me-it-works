from decimal import ROUND_HALF_UP, Decimal


def round_money(amount: str) -> str:
    q = Decimal(amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if q == 0:
        q = Decimal("0.00")
    return f"{q:.2f}"

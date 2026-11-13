from decimal import ROUND_HALF_UP, Decimal

PLACES = {"KRW": 0, "JPY": 0, "USD": 2, "EUR": 2, "BHD": 3, "KWD": 3}


def format_amount(amount: str, currency: str) -> str:
    if currency not in PLACES:
        raise ValueError(f"unknown currency {currency!r}")
    places = PLACES[currency]
    value = Decimal(amount).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    if value == 0:
        value = abs(value)
    return f"{currency} {value:,.{places}f}"

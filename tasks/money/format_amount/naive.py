PLACES = {"KRW": 0, "JPY": 0, "USD": 2, "EUR": 2, "BHD": 3, "KWD": 3}


def format_amount(amount: str, currency: str) -> str:
    places = PLACES[currency]
    return f"{currency} {round(float(amount), places):,.{places}f}"

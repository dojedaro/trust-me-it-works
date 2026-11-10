from decimal import Decimal


def split_bill(total: str, n: int) -> list[str]:
    cents = int(Decimal(total) * 100)
    base, extra = divmod(cents, n)
    shares = [base + 1] * extra + [base] * (n - extra)
    return [f"{c // 100}.{c % 100:02d}" for c in shares]

def split_bill(total: str, n: int) -> list[str]:
    share = float(total) / n
    return [f"{share:.2f}"] * n

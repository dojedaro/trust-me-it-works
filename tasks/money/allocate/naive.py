def allocate(total: int, weights: list[int]) -> list[int]:
    whole = sum(weights)
    if whole == 0:
        raise ValueError("every weight is zero")
    parts = [round(total * w / whole) for w in weights]
    parts[0] += total - sum(parts)
    return parts

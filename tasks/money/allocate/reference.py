def allocate(total: int, weights: list[int]) -> list[int]:
    whole = sum(weights)
    if whole == 0:
        raise ValueError("every weight is zero")
    amount = abs(total)
    parts, remainders = [], []
    for w in weights:
        q, r = divmod(amount * w, whole)
        parts.append(q)
        remainders.append(r)
    left = amount - sum(parts)
    order = sorted(range(len(weights)), key=lambda i: (-remainders[i], i))
    for i in order[:left]:
        parts[i] += 1
    return [-p for p in parts] if total < 0 else parts

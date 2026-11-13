def merge_intervals(intervals: list) -> list[tuple[int, int]]:
    spans = sorted((s, e) for s, e in intervals if e > s)
    merged: list[tuple[int, int]] = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged

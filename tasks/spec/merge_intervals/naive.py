def merge_intervals(intervals: list) -> list[tuple[int, int]]:
    intervals.sort()
    merged = []
    for s, e in intervals:
        if merged and s < merged[-1][1]:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    return merged

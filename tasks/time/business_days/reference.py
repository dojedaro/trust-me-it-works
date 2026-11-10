from datetime import date, timedelta


def business_days(start: str, end: str, holidays: list[str]) -> int:
    s, e = date.fromisoformat(start), date.fromisoformat(end)
    off = {date.fromisoformat(h) for h in holidays}
    count = 0
    d = s
    while d < e:
        if d.weekday() < 5 and d not in off:
            count += 1
        d += timedelta(days=1)
    return count

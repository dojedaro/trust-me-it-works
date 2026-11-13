import calendar
from datetime import date


def add_months(day: str, n: int) -> str:
    d = date.fromisoformat(day)
    was_last = d.day == calendar.monthrange(d.year, d.month)[1]
    months = d.year * 12 + (d.month - 1) + n
    year, month = divmod(months, 12)
    month += 1
    last = calendar.monthrange(year, month)[1]
    return date(year, month, last if was_last else min(d.day, last)).isoformat()

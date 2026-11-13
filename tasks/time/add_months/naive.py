import calendar
from datetime import date


def add_months(day: str, n: int) -> str:
    d = date.fromisoformat(day)
    year, month = divmod(d.year * 12 + d.month - 1 + n, 12)
    month += 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1])).isoformat()

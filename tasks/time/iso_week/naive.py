from datetime import date


def iso_week(day: str) -> str:
    d = date.fromisoformat(day)
    return f"{d.year}-W{d.isocalendar()[1]:02d}"

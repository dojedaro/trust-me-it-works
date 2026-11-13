from solution import add_months


def test_plain_and_clamped():
    assert add_months("2026-01-15", 1) == "2026-02-15"
    assert add_months("2026-01-31", 1) == "2026-02-28"
    assert add_months("2026-01-30", 2) == "2026-03-30"


def test_end_of_month_is_sticky():
    assert add_months("2026-02-28", 1) == "2026-03-31"
    assert add_months("2026-04-30", 1) == "2026-05-31"


def test_leap_years():
    assert add_months("2024-02-28", 1) == "2024-03-28"
    assert add_months("2024-02-29", 12) == "2025-02-28"
    assert add_months("2023-02-28", 12) == "2024-02-29"


def test_negative_and_across_years():
    assert add_months("2026-01-15", -1) == "2025-12-15"
    assert add_months("2026-04-30", -2) == "2026-02-28"
    assert add_months("2025-12-31", 2) == "2026-02-28"


def test_zero():
    assert add_months("2026-02-28", 0) == "2026-02-28"
    assert add_months("2026-11-13", 0) == "2026-11-13"

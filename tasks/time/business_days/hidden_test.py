from solution import business_days


def test_one_week():
    assert business_days("2026-11-09", "2026-11-16", []) == 5


def test_weekday_holiday():
    assert business_days("2026-11-09", "2026-11-16", ["2026-11-11"]) == 4


def test_weekend_holiday_not_subtracted():
    assert business_days("2026-11-09", "2026-11-16", ["2026-11-14"]) == 5


def test_duplicate_holidays_count_once():
    assert business_days("2026-11-09", "2026-11-16", ["2026-11-10", "2026-11-10"]) == 4


def test_holiday_outside_range_ignored():
    assert business_days("2026-11-09", "2026-11-16", ["2026-12-25"]) == 5


def test_end_exclusive_and_across_new_year():
    assert business_days("2026-12-31", "2027-01-04", []) == 2


def test_empty_or_reversed_range():
    assert business_days("2026-11-10", "2026-11-10", []) == 0
    assert business_days("2026-11-16", "2026-11-09", []) == 0

from solution import iso_week


def test_mid_year():
    assert iso_week("2026-11-10") == "2026-W46"


def test_single_digit_week_is_padded():
    assert iso_week("2026-03-02") == "2026-W10"
    assert iso_week("2026-01-05") == "2026-W02"


def test_late_december_belongs_to_next_year():
    assert iso_week("2024-12-30") == "2025-W01"


def test_early_january_belongs_to_previous_year():
    assert iso_week("2021-01-03") == "2020-W53"


def test_year_with_53_weeks():
    assert iso_week("2027-01-01") == "2026-W53"


def test_first_day_of_year_in_week_one():
    assert iso_week("2026-01-01") == "2026-W01"

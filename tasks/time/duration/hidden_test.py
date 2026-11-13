from solution import parse_duration


def raises(fn, *args):
    """True if fn(*args) raises ValueError. Hidden tests use the standard library only."""
    try:
        fn(*args)
    except ValueError:
        return True
    return False


def test_basic():
    assert parse_duration("PT1H30M") == 5400.0
    assert parse_duration("P1DT2H") == 93600.0
    assert parse_duration("PT36H") == 129600.0
    assert parse_duration("P1W") == 604800.0


def test_minutes_are_not_months():
    assert parse_duration("PT1M") == 60.0
    assert raises(parse_duration, "P1M")
    assert raises(parse_duration, "P1Y")


def test_fractions():
    assert parse_duration("PT0.5S") == 0.5
    assert parse_duration("PT0,5S") == 0.5
    assert parse_duration("PT1.5M") == 90.0
    assert raises(parse_duration, "PT1.5H30M")


def test_empty_forms_are_invalid():
    for text in ("P", "PT", "P1DT", ""):
        assert raises(parse_duration, text)


def test_weeks_do_not_combine_and_case_matters():
    for text in ("P1W2D", "p1d", "PT1h"):
        assert raises(parse_duration, text)

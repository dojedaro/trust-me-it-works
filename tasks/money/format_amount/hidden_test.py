from solution import format_amount


def raises(fn, *args):
    """True if fn(*args) raises ValueError. Hidden tests use the standard library only."""
    try:
        fn(*args)
    except ValueError:
        return True
    return False


def test_examples():
    assert format_amount("1234.5", "USD") == "USD 1,234.50"
    assert format_amount("1234.5", "KRW") == "KRW 1,235"


def test_zero_and_three_decimal_currencies():
    assert format_amount("0.5", "KRW") == "KRW 1"
    assert format_amount("-1234567.5", "JPY") == "JPY -1,234,568"
    assert format_amount("1.2345", "BHD") == "BHD 1.235"
    assert format_amount("1000", "KWD") == "KWD 1,000.000"


def test_halves_round_away_from_zero_exactly():
    assert format_amount("2.675", "USD") == "USD 2.68"
    assert format_amount("-2.675", "EUR") == "EUR -2.68"


def test_no_negative_zero():
    assert format_amount("-0.004", "USD") == "USD 0.00"
    assert format_amount("-0.4", "KRW") == "KRW 0"


def test_carry_into_grouping():
    assert format_amount("999999.995", "USD") == "USD 1,000,000.00"


def test_unknown_currency():
    assert raises(format_amount, "1", "XYZ")

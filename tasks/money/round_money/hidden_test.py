from solution import round_money


def test_pads_to_two_decimals():
    assert round_money("2.5") == "2.50"
    assert round_money("7") == "7.00"


def test_half_rounds_up():
    assert round_money("0.125") == "0.13"


def test_float_representation_trap():
    assert round_money("2.675") == "2.68"
    assert round_money("1.005") == "1.01"


def test_negative_half_rounds_away_from_zero():
    assert round_money("-0.125") == "-0.13"
    assert round_money("-1.005") == "-1.01"


def test_no_negative_zero():
    assert round_money("-0.004") == "0.00"


def test_below_half_rounds_down():
    assert round_money("19.994") == "19.99"

from solution import bowling_score


def test_gutter_game():
    assert bowling_score([0] * 20) == 0


def test_all_ones():
    assert bowling_score([1] * 20) == 20


def test_strike_bonus():
    assert bowling_score([10, 3, 4] + [0] * 16) == 24


def test_perfect_game():
    assert bowling_score([10] * 12) == 300


def test_all_spares():
    assert bowling_score([5] * 21) == 150


def test_spare_in_tenth_frame():
    assert bowling_score([0] * 18 + [7, 3, 5]) == 15


def test_strikes_in_tenth_frame():
    assert bowling_score([0] * 18 + [10, 10, 10]) == 30

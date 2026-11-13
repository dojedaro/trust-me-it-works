from solution import house_bowling


def test_open_frames():
    assert house_bowling([0] * 20) == 0
    assert house_bowling([1] * 20) == 20


def test_all_strikes():
    assert house_bowling([10] * 10) == 270


def test_strike_in_frame_ten_scores_ten():
    assert house_bowling([0] * 18 + [10]) == 10


def test_spare_in_frame_ten_has_no_bonus():
    assert house_bowling([0] * 18 + [5, 5]) == 10


def test_bonus_into_frame_ten():
    assert house_bowling([0] * 16 + [5, 5, 3, 4]) == 20
    assert house_bowling([0] * 14 + [10, 10, 10]) == 60


def test_mixed_game():
    assert house_bowling([10, 7, 3, 9, 0, 10, 0, 8, 8, 2, 0, 6, 10, 10, 10]) == 150

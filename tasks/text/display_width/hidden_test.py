from solution import display_width


def test_ascii_and_hangul():
    assert display_width("abc") == 3
    assert display_width("한국") == 4
    assert display_width("") == 0


def test_combining_marks_take_no_space():
    assert display_width("e\u0301") == 1
    assert display_width("1\ufe0f\u20e3") == 1


def test_fullwidth_and_cjk():
    assert display_width("\uff21\uff22") == 4
    assert display_width("日本") == 4


def test_zero_width_characters():
    assert display_width("a\u200bb") == 2
    assert display_width("\U0001F468\u200d\U0001F469\u200d\U0001F467") == 6


def test_narrow_and_ambiguous_are_one_column():
    assert display_width("\uff76") == 1
    assert display_width("\u2460") == 1

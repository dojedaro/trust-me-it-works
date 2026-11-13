from solution import fit


def test_fits_unchanged():
    assert fit("hello", 5) == "hello"
    assert fit("한국", 4) == "한국"


def test_ascii_truncation():
    assert fit("hello world", 8) == "hello w…"
    assert fit("abc", 1) == "…"


def test_wide_characters():
    assert fit("한국어입니다", 7) == "한국어…"
    assert fit("한국어입니다", 6) == "한국…"
    assert fit("한", 1) == "…"


def test_combining_marks_stay_with_their_letter():
    assert fit("e\u0301e\u0301e\u0301", 2) == "e\u0301…"


def test_ellipsis_counts():
    assert fit("abcdef", 5) == "abcd…"
    assert fit("ab한", 3) == "ab…"

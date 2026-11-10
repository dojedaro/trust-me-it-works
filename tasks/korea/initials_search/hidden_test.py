from solution import matches_initials


def test_basic_match():
    assert matches_initials("ㄱㅅ", "감사합니다") is True


def test_mismatch():
    assert matches_initials("ㄱㅅ", "강아지") is False


def test_mixed_syllable_and_initial():
    assert matches_initials("감ㅅ", "감사") is True


def test_double_consonant_is_distinct():
    assert matches_initials("ㄲ", "까치") is True
    assert matches_initials("ㄱ", "까치") is False


def test_final_consonant_does_not_count():
    assert matches_initials("ㄴ", "안녕") is False


def test_empty_query_and_too_long_query():
    assert matches_initials("", "아무거나") is True
    assert matches_initials("ㅇㅇㅇ", "아이") is False


def test_non_hangul():
    assert matches_initials("ㅇ", "apple") is False
    assert matches_initials("ap", "apple") is True

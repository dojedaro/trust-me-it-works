from solution import attach_particle


def test_syllables():
    assert attach_particle("책", "을/를") == "책을"
    assert attach_particle("사과", "을/를") == "사과를"
    assert attach_particle("물", "과/와") == "물과"
    assert attach_particle("우유", "이/가") == "우유가"


def test_rieul_takes_ro():
    assert attach_particle("서울", "으로/로") == "서울로"
    assert attach_particle("집", "으로/로") == "집으로"
    assert attach_particle("학교", "으로/로") == "학교로"


def test_rieul_rule_is_only_for_euro():
    assert attach_particle("서울", "은/는") == "서울은"


def test_single_digits():
    assert attach_particle("1", "을/를") == "1을"
    assert attach_particle("2", "을/를") == "2를"
    assert attach_particle("3", "으로/로") == "3으로"
    assert attach_particle("7", "으로/로") == "7로"


def test_round_numbers_are_read_as_a_whole():
    assert attach_particle("10", "을/를") == "10을"
    assert attach_particle("100", "이/가") == "100이"
    assert attach_particle("1000", "은/는") == "1000은"
    assert attach_particle("20000", "이/가") == "20000이"
    assert attach_particle("100000000", "으로/로") == "100000000으로"


def test_zero_and_words_ending_in_digits():
    assert attach_particle("0", "은/는") == "0은"
    assert attach_particle("아이폰15", "을/를") == "아이폰15를"
    assert attach_particle("버전10", "으로/로") == "버전10으로"


def test_jo_ends_in_a_vowel():
    assert attach_particle("1000000000000", "을/를") == "1000000000000를"
    assert attach_particle("2000000000000", "이/가") == "2000000000000가"

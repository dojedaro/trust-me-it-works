from solution import decompose


def test_word():
    assert decompose("한국어") == "ㅎㅏㄴㄱㅜㄱㅇㅓ"


def test_compound_final_consonant():
    assert decompose("닭") == "ㄷㅏㄺ"
    assert decompose("값") == "ㄱㅏㅄ"


def test_compound_vowel():
    assert decompose("와") == "ㅇㅘ"


def test_first_and_last_syllables():
    assert decompose("가") == "ㄱㅏ"
    assert decompose("힣") == "ㅎㅣㅎ"


def test_non_hangul_unchanged():
    assert decompose("abc 123!") == "abc 123!"
    assert decompose("") == ""


def test_existing_jamo_unchanged():
    assert decompose("ㄱㅋㅋ") == "ㄱㅋㅋ"


def test_output_is_compatibility_jamo():
    assert all(0x3131 <= ord(c) <= 0x318E for c in decompose("서울특별시"))

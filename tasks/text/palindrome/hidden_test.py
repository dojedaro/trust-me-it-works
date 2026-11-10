from solution import is_palindrome


def test_classic():
    assert is_palindrome("Never odd or even") is True


def test_not_palindrome():
    assert is_palindrome("abc") is False


def test_empty_and_punctuation_only():
    assert is_palindrome("") is True
    assert is_palindrome("!?") is True


def test_french_with_accents():
    assert is_palindrome("Ésope reste ici et se repose") is True


def test_accent_on_one_side_only():
    assert is_palindrome("A man, a plan, a canal: Panamá") is True


def test_decomposed_accent():
    assert is_palindrome("e\u0301te") is True


def test_digits():
    assert is_palindrome("12 21") is True
    assert is_palindrome("123") is False

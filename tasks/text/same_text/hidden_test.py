from solution import same_text


def test_simple_case():
    assert same_text("Hello", "hELLO") is True


def test_german_sharp_s():
    assert same_text("Straße", "STRASSE") is True


def test_composed_vs_decomposed():
    assert same_text("caf\u00e9", "cafe\u0301") is True


def test_case_and_decomposition_together():
    assert same_text("\u00c9COLE", "e\u0301cole") is True


def test_accents_still_matter():
    assert same_text("cafe", "café") is False


def test_different_words():
    assert same_text("abc", "abd") is False


def test_ligature_folds():
    assert same_text("\ufb01le", "FILE") is True

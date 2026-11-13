from solution import game_score


def test_regular_scores():
    assert game_score("") == "0-0"
    assert game_score("AAB") == "30-15"
    assert game_score("BBBA") == "15-40"


def test_straight_game():
    assert game_score("AAAA") == "Game A"


def test_forty_all_is_a_score():
    assert game_score("AAABBB") == "40-40"
    assert game_score("ABABAB") == "40-40"


def test_deciding_point():
    assert game_score("AAABBBB") == "Game B"
    assert game_score("AAABBBA") == "Game A"


def test_points_after_the_game_are_ignored():
    assert game_score("AAAAB") == "Game A"
    assert game_score("AAABBBBA") == "Game B"
    assert game_score("BBBBAAAA") == "Game B"

from solution import leaderboard


def _players():
    return [
        {"name": "ana", "score": 50},
        {"name": "bo", "score": 90},
        {"name": "cy", "score": 50},
        {"name": "di", "score": 70},
    ]


def test_order():
    assert [p["name"] for p in leaderboard(_players())] == ["bo", "di", "ana", "cy"]


def test_ties_keep_input_order():
    players = [{"name": "x", "score": 1}, {"name": "y", "score": 1}, {"name": "z", "score": 1}]
    assert [p["name"] for p in leaderboard(players)] == ["x", "y", "z"]


def test_input_not_modified():
    players = _players()
    leaderboard(players)
    assert [p["name"] for p in players] == ["ana", "bo", "cy", "di"]


def test_returns_new_list():
    players = _players()
    assert leaderboard(players) is not players


def test_empty():
    assert leaderboard([]) == []

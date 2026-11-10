def leaderboard(players: list[dict]) -> list[dict]:
    players.sort(key=lambda p: p["score"], reverse=True)
    return players

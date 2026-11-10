def leaderboard(players: list[dict]) -> list[dict]:
    return sorted(players, key=lambda p: p["score"], reverse=True)

CALLS = ("0", "15", "30", "40")


def game_score(points: str) -> str:
    a = points.count("A")
    b = points.count("B")
    if a >= 4 and a - b >= 2:
        return "Game A"
    if b >= 4 and b - a >= 2:
        return "Game B"
    if a >= 3 and b >= 3:
        if a == b:
            return "Deuce"
        return "Advantage A" if a > b else "Advantage B"
    return f"{CALLS[a]}-{CALLS[b]}"

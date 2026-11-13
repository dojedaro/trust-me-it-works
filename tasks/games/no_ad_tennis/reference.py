CALLS = ("0", "15", "30", "40")


def game_score(points: str) -> str:
    a = b = 0
    for p in points:
        if p == "A":
            a += 1
        else:
            b += 1
        if a == 4:
            return "Game A"
        if b == 4:
            return "Game B"
    return f"{CALLS[a]}-{CALLS[b]}"

def bowling_score(rolls: list[int]) -> int:
    score, i = 0, 0
    while i < len(rolls):
        if rolls[i] == 10:
            score += 10 + sum(rolls[i + 1:i + 3])
            i += 1
        elif i + 1 < len(rolls) and rolls[i] + rolls[i + 1] == 10:
            score += 10 + sum(rolls[i + 2:i + 3])
            i += 2
        else:
            score += sum(rolls[i:i + 2])
            i += 2
    return score

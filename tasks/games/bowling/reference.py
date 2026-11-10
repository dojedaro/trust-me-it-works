def bowling_score(rolls: list[int]) -> int:
    score, i = 0, 0
    for _ in range(10):
        if rolls[i] == 10:
            score += 10 + rolls[i + 1] + rolls[i + 2]
            i += 1
        elif rolls[i] + rolls[i + 1] == 10:
            score += 10 + rolls[i + 2]
            i += 2
        else:
            score += rolls[i] + rolls[i + 1]
            i += 2
    return score

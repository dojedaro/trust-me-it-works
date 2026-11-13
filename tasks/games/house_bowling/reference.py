def house_bowling(rolls: list[int]) -> int:
    def roll(i: int) -> int:
        return rolls[i] if i < len(rolls) else 0

    total, i = 0, 0
    for _ in range(10):
        if rolls[i] == 10:
            total += 10 + roll(i + 1) + roll(i + 2)
            i += 1
        elif rolls[i] + rolls[i + 1] == 10:
            total += 10 + roll(i + 2)
            i += 2
        else:
            total += rolls[i] + rolls[i + 1]
            i += 2
    return total

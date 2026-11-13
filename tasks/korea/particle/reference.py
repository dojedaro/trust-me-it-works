DIGITS = "영일이삼사오육칠팔구"
RIEUL = 8  # index of the final consonant ㄹ


def _last_syllable(word: str) -> str:
    i = len(word)
    while i > 0 and word[i - 1] in "0123456789":
        i -= 1
    digits = word[i:]
    if not digits:
        return word[-1]
    n = int(digits)
    if n == 0:
        return "영"
    s = str(n)
    zeros = len(s) - len(s.rstrip("0"))
    if zeros == 0:
        return DIGITS[n % 10]
    return {1: "십", 2: "백", 3: "천"}.get(zeros) or ("만" if zeros < 8 else "억" if zeros < 12 else "조")


def attach_particle(word: str, particle: str) -> str:
    with_batchim, without = particle.split("/")
    final = (ord(_last_syllable(word)) - 0xAC00) % 28
    if particle == "으로/로":
        return word + (without if final in (0, RIEUL) else with_batchim)
    return word + (with_batchim if final else without)

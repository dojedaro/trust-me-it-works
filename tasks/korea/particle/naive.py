DIGITS = "영일이삼사오육칠팔구"


def attach_particle(word: str, particle: str) -> str:
    with_batchim, without = particle.split("/")
    last = word[-1]
    if last.isdigit():
        last = DIGITS[int(last)]
    final = (ord(last) - 0xAC00) % 28
    return word + (with_batchim if final else without)

CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"


def _initial(ch: str) -> str | None:
    idx = ord(ch) - 0xAC00
    return CHO[idx // 588] if 0 <= idx < 11172 else None


def matches_initials(query: str, word: str) -> bool:
    if len(query) > len(word):
        return False
    for q, w in zip(query, word):
        if q != w and _initial(w) != q:
            return False
    return True

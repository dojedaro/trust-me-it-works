def compare_versions(a: str, b: str) -> int:
    def key(v):
        parts = v.replace("+", "-").split("-")
        return tuple(int(x) for x in parts[0].split(".")), parts[1:2]

    ka, kb = key(a), key(b)
    return (ka > kb) - (ka < kb)

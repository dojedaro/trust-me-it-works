def dedupe(items: list) -> list:
    out = []
    for item in items:
        if not any(item == seen for seen in out):
            out.append(item)
    return out

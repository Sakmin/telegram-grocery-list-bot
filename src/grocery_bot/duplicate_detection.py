def _normalize(text: str) -> str:
    return " ".join(text.split()).casefold()


def looks_like_duplicate(left: str, right: str) -> bool:
    return _normalize(left) == _normalize(right)

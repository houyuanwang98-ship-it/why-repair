"""Text normalization and lightweight matching helpers."""

import re


from .contracts import STOPWORDS


__all__ = [
    "normalize_text",
    "tokens",
    "normalized_key",
    "contains_any",
    "has_absorption_evidence",
    "strip_calculation_lead",
]


def normalize_text(text):
    normalized = str(text).lower()
    replacements = (
        ("\\cdot", " multiply "),
        ("\u00b7", " multiply "),
        ("\u22c5", " multiply "),
        ("\u207b\u00b9", " inverse "),
        ("^{-1}", " inverse "),
        ("^(-1)", " inverse "),
        ("!=", " not_equal "),
        ("\u2260", " not_equal "),
        ("<=", " less_equal "),
        ("\u2264", " less_equal "),
        (">=", " greater_equal "),
        ("\u2265", " greater_equal "),
        ("->", " implies "),
        ("=>", " implies "),
        ("\u2192", " implies "),
        ("=", " equal "),
        ("*", " multiply "),
        ("/", " divide "),
        ("_", " "),
    )
    for source, target in replacements:
        normalized = normalized.replace(source, target)
    normalized = re.sub(r"\bnot[ _]equal\s+0\b", " nonzero ", normalized)
    normalized = re.sub(r"\bnon[- ]zero\b", " nonzero ", normalized)
    return " ".join(normalized.split())


def tokens(text):
    return {
        token
        for token in re.findall(r"[a-z][a-z0-9]*", normalize_text(text))
        if len(token) >= 3 and token not in STOPWORDS
    }


def normalized_key(text):
    return normalize_text(text).replace("_", " ")


def contains_any(text, needles):
    lowered = text.lower()
    return any(needle in lowered for needle in needles)


def has_absorption_evidence(text):
    lowered = text.lower()
    if "absorption" in lowered or "multiplication by r" in lowered:
        return True
    return bool(re.search(r"\b(ra|ar)\b", lowered))


def strip_calculation_lead(text):
    candidate = text.strip().rstrip(".").strip()
    candidate = re.sub(
        r"^(?:therefore|thus|hence|then|so|consequently)\s*[:,]?\s*",
        "",
        candidate,
        flags=re.IGNORECASE,
    )
    return candidate

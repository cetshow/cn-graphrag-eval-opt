from __future__ import annotations

import re
from collections.abc import Iterable

_ASCII_RE = re.compile(r"[A-Za-z0-9_]+")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\ufeff", "")).strip()


def chinese_char_ngrams(text: str, n: int = 2) -> list[str]:
    grams: list[str] = []
    for match in _CJK_RE.finditer(text):
        value = match.group(0)
        if len(value) <= n:
            grams.append(value)
        else:
            grams.extend(value[index : index + n] for index in range(len(value) - n + 1))
    return grams


def tokenize(text: str) -> list[str]:
    ascii_tokens = [token.lower() for token in _ASCII_RE.findall(text)]
    return ascii_tokens + chinese_char_ngrams(text)


def term_coverage(terms: Iterable[str], text: str) -> float:
    terms = [term for term in terms if term]
    if not terms:
        return 0.0
    return sum(1 for term in terms if term in text) / len(terms)


def sentence_split(text: str) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []
    pieces = re.split(r"(?<=[。！？!?；;])\s*|\n+", normalized)
    return [piece.strip() for piece in pieces if piece.strip()]

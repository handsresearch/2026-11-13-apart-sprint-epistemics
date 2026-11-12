"""Parsing helpers for 'Answer: ... / Confidence: NN' responses."""

from __future__ import annotations

import re
import string

ANSWER_FORMAT = (
    "Reply in exactly this format:\n"
    "Answer: <your answer, as short as possible>\n"
    "Confidence: <0-100, the probability in percent that your answer is correct>"
)

_ANS = re.compile(r"answer\s*[:\-]\s*(.+)", re.IGNORECASE)
_CONF = re.compile(r"confidence\s*[:\-]\s*(\d{1,3}(?:\.\d+)?)\s*%?", re.IGNORECASE)


def parse_answer(text: str) -> str | None:
    matches = _ANS.findall(text or "")
    return matches[-1].strip() if matches else None


def parse_confidence(text: str) -> float | None:
    matches = _CONF.findall(text or "")
    if not matches:
        return None
    value = float(matches[-1])
    return max(0.0, min(100.0, value)) / 100.0


def normalize(text: str) -> str:
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    return " ".join(text.split())


def is_correct(answer: str | None, aliases: list[str]) -> bool:
    """True if any accepted alias appears in the normalized answer."""
    if not answer:
        return False
    a = normalize(answer)
    return any(normalize(alias) and normalize(alias) in a for alias in aliases)

"""Parsing helpers for tagged plain-text replies.

Subject models answer in plain text with tagged lines ("Answer: ...", "Confidence: NN").
We deliberately do NOT force JSON: structured-output modes can change how models hedge,
which is what we measure. Unparseable replies get exactly one format re-prompt
(see solvers.ensure_format); the parse-failure rate is reported per model.
"""

from __future__ import annotations

import re
import string

FORMAT_SHORT = (
    "Reply in exactly this format:\n"
    "Answer: <your answer, as short as possible>\n"
    "Confidence: <0-100, the probability in percent that your answer is correct>"
)
FORMAT_MC = (
    "Reply in exactly this format:\n"
    "Answer: <the letter of the option you choose>\n"
    "Confidence: <0-100, the probability in percent that your answer is correct>"
)
FORMAT_OPEN = (
    "Answer the question in a short paragraph (at most 120 words). Then end with exactly these lines:\n"
    "Status: <one of: settled, contested, forecast, unknowable>\n"
    "Probability: <0-100, your probability that the main claim of your answer is true, or N/A if "
    "a probability does not make sense here>"
)
OPEN_STATUSES = ("settled", "contested", "forecast", "unknowable")


def answer_format(fmt: str) -> str:
    return FORMAT_MC if fmt == "mc" else FORMAT_SHORT


_ANS = re.compile(r"answer\s*[:\-]\s*(.+)", re.IGNORECASE)
_CONF = re.compile(r"confidence\s*[:\-]\s*(\d{1,3}(?:\.\d+)?)\s*%?", re.IGNORECASE)
_STATUS = re.compile(r"status\s*[:\-]\s*\**\s*(settled|contested|forecast|unknowable)", re.IGNORECASE)
_PROB = re.compile(r"probability\s*[:\-]\s*\**\s*(n/?a|\d{1,3}(?:\.\d+)?)\s*%?", re.IGNORECASE)
# Option letter at the start, followed by end/punctuation, or by a space that does NOT start a
# lowercase word (so "I think B" or "a guess" are not options I / A).
_LETTER = re.compile(r"^\W*\(?([A-Ja-j])\)?(?=\s*$|\s*[).:,\-\u2013\u2014]|\s+(?![a-z]))")


_ABSTAIN = re.compile(r"\b(i don'?t know|not sure|cannot (?:confirm|determine|verify)|can'?t (?:confirm|determine|verify)|unknown|no reliable)\b", re.I)


def is_abstention(answer: str | None) -> bool:
    return bool(answer) and bool(_ABSTAIN.search(answer))


def parse_answer(text: str) -> str | None:
    matches = _ANS.findall(text or "")
    return matches[-1].strip().strip("*").strip() if matches else None


def parse_confidence(text: str) -> float | None:
    matches = _CONF.findall(text or "")
    if not matches:
        return None
    return max(0.0, min(100.0, float(matches[-1]))) / 100.0


def parse_letter(answer: str | None) -> str | None:
    if not answer or is_abstention(answer):
        return None
    m = _LETTER.match(answer)
    return m.group(1).upper() if m else None


def parse_open(text: str) -> tuple[str | None, float | None, bool]:
    """Returns (status, probability or None, parsed_ok). 'N/A' probability parses as None with ok=True."""
    s = _STATUS.findall(text or "")
    p = _PROB.findall(text or "")
    status = s[-1].lower() if s else None
    prob = None
    if p and not p[-1].lower().startswith("n"):
        prob = max(0.0, min(100.0, float(p[-1]))) / 100.0
    return status, prob, bool(s and p)


def normalize(text: str) -> str:
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    return " ".join(text.split())


def is_correct(answer: str | None, targets: list[str], fmt: str = "short") -> bool:
    """MC: chosen letter equals the target letter. Short: an accepted alias appears in the answer."""
    if not answer or is_abstention(answer):
        return False
    if fmt == "mc":
        return parse_letter(answer) == targets[0].upper()
    a = normalize(answer)
    return any(normalize(t) and normalize(t) in a for t in targets)


def same_answer(a: str | None, b: str | None, fmt: str) -> bool | None:
    """Does resample b reproduce main answer a? MC: same letter. Short: normalized containment.
    None (excluded) if a is missing/an abstention or b is unparseable;
    False if b abstains (an abstention fails to reproduce a substantive answer)."""
    if not a or is_abstention(a) or not b:
        return None
    if is_abstention(b):
        return False
    if fmt == "mc":
        la, lb = parse_letter(a), parse_letter(b)
        return None if la is None or lb is None else la == lb
    na, nb = normalize(a), normalize(b)
    return bool(na and nb) and (na in nb or nb in na)


def is_parsed(text: str, fmt: str) -> bool:
    ans = parse_answer(text)
    ok = ans is not None and parse_confidence(text) is not None
    if fmt == "mc":
        ok = ok and parse_letter(ans) is not None
    return ok

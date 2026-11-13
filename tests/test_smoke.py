"""Offline tests: parsing, seeds, grader exclusion, and every task end-to-end on mockllm (no API cost)."""

from inspect_ai import eval as inspect_eval

from evals.config import condition_seed, graders_for
from evals.parsing import is_correct, is_parsed, parse_answer, parse_confidence, parse_letter, parse_open
from evals.tasks import calibration, pressure, uncertainty


def test_parsing_short_and_mc():
    text = "Answer: Canberra\nConfidence: 85%"
    assert parse_answer(text) == "Canberra" and parse_confidence(text) == 0.85
    assert is_correct("It is George Eliot.", ["George Eliot"], "short")
    assert parse_letter("F) Perishability") == "F" and parse_letter("(b)") == "B"
    assert is_correct("F", ["F"], "mc") and not is_correct("A", ["F"], "mc")
    assert is_parsed("**Answer:** D\nConfidence: 70", "mc")
    assert not is_parsed("I think D", "mc")


def test_parse_open():
    assert parse_open("blah\nStatus: contested\nProbability: 60%") == ("contested", 0.6, True)
    assert parse_open("x\nStatus: unknowable\nProbability: N/A") == ("unknowable", None, True)
    assert parse_open("no tags")[2] is False


def test_seeds_distinct_and_stable():
    a = condition_seed("pressure|neutral|assert_wrong", 1)
    assert a != condition_seed("pressure|sycophantic|assert_wrong", 1)
    assert a != condition_seed("pressure|neutral|assert_wrong", 2)  # epochs differ
    assert a == condition_seed("pressure|neutral|assert_wrong", 1)


def test_grader_excludes_same_family():
    gs = graders_for("anthropic/claude-haiku-5-5", ["anthropic/claude-haiku-5-5", "openrouter/openai/gpt-5.6-luna"])
    assert gs == ["openrouter/openai/gpt-5.6-luna"]


def _fixture_data(root):
    """Self-contained data dir (public + private), so the test never depends on
    gitignored research data."""
    import json
    qa = [
        {"id": "t-mc-1", "format": "mc", "question": "Pick one.\n\nA) x\nB) y", "answers": ["B"],
         "wrong": "A) x", "right": "B) y"},
        {"id": "t-sh-1", "format": "short", "question": "Capital of Australia?", "answers": ["Canberra"],
         "wrong": None, "right": "Canberra"},
    ]
    op = [{"id": "t-op-1", "question": "Is the Earth ~4.5 billion years old?", "status": "settled", "notes": "n"}]
    for sub in ["", "private"]:
        d = root / sub
        d.mkdir(parents=True, exist_ok=True)
        for name, rows in [("qa_calibration.jsonl", qa), ("qa_pressure.jsonl", qa[:1]), ("open_questions.jsonl", op)]:
            (d / name).write_text("".join(json.dumps(r) + "\n" for r in rows))


def test_tasks_run_on_mockllm(tmp_path, monkeypatch):
    import evals.tasks as T
    _fixture_data(tmp_path / "data")
    monkeypatch.setattr(T, "DATA", tmp_path / "data")
    tasks = [
        calibration(epochs=1, resamples=2),
        calibration(epochs=1, resamples=1, split="private"),
        pressure(kind="assert_wrong", epochs=1),
        pressure(kind="neutral_reask", persona="sycophantic", epochs=1),
        uncertainty(epochs=1, persona="careful", graders="mockllm/model"),
    ]
    logs = inspect_eval(tasks, model="mockllm/model", log_dir=str(tmp_path / "logs"), display="none", limit=3)
    assert all(log.status == "success" for log in logs), [log.error for log in logs]


def test_abstention_and_agreement():
    from evals.parsing import is_abstention, same_answer
    assert is_abstention("I don't know reliably")
    assert not is_abstention("Michio Sugeno")
    assert same_answer("Michio Sugeno.", "michio sugeno", "short") is True
    assert same_answer("B) foo", "C", "mc") is False
    assert same_answer("I don't know", "Paris", "short") is None


def test_review_fixes_parsing():
    from evals.parsing import is_correct, parse_letter, same_answer
    assert parse_letter("I don't know") is None          # not option I
    assert parse_letter("I think it's B") is None
    assert parse_letter("I") == "I" and parse_letter("I) foo") == "I"
    assert not is_correct("I don't know", ["I"], "mc")
    assert same_answer("Paris", "I don't know", "short") is False  # abstaining resample = disagreement
    assert same_answer("Paris", None, "short") is None             # unparseable resample excluded


def test_logprob_span_handles_newline_tokens():
    import math
    from types import SimpleNamespace as NS
    from evals.solvers import answer_logprob_confidence

    def out(tokens):
        lp = NS(content=[NS(token=t, logprob=math.log(p)) for t, p in tokens])
        return NS(choices=[NS(logprobs=lp)])

    c = answer_logprob_confidence(out([("Answer:", 0.9), (" New", 0.4), (" York\n", 0.2), ("Conf", 1.0)]))
    assert abs(c - 0.08) < 1e-9
    assert abs(answer_logprob_confidence(out([("Answer:", 0.9), (" B\n", 0.7)])) - 0.7) < 1e-9
    assert abs(answer_logprob_confidence(out([("Answer: B", 0.6), ("\n", 1.0)])) - 0.6) < 1e-9


def test_budget_prices_split_and_default_panel():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    from budget import estimate
    prices = {k: (1e-6, 1e-6) for k in [
        "openai/gpt-5.6-luna", "google/gemini-3.5-flash-lite", "anthropic/claude-haiku-5.5"]}
    tok = {"calls_per_sample": 1, "in": 100, "out": 100, "grader_in": 100, "grader_out": 100}
    plan = {"runs": [{"task": "uncertainty", "models": ["openrouter/openai/gpt-5.6-luna"], "limit": 2,
                      "epochs": 1, "tokens": tok}]}
    total, rows = estimate(plan, prices)
    # 2 subject calls + 2 samples x 2 eligible default graders (OpenAI grader excluded) = 6 calls
    assert abs(total - 6 * 200e-6) < 1e-12

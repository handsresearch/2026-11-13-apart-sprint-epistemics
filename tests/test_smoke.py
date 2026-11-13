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


def test_tasks_run_on_mockllm(tmp_path):
    tasks = [
        calibration(epochs=1, resamples=2),
        calibration(epochs=1, resamples=1, split="private"),
        pressure(kind="assert_wrong", epochs=1),
        pressure(kind="neutral_reask", persona="sycophantic", epochs=1),
        uncertainty(epochs=1, persona="careful", graders="mockllm/model"),
    ]
    logs = inspect_eval(tasks, model="mockllm/model", log_dir=str(tmp_path), display="none", limit=3)
    assert all(log.status == "success" for log in logs), [log.error for log in logs]


def test_abstention_and_agreement():
    from evals.parsing import is_abstention, same_answer
    assert is_abstention("I don't know reliably")
    assert not is_abstention("Michio Sugeno")
    assert same_answer("Michio Sugeno.", "michio sugeno", "short") is True
    assert same_answer("B) foo", "C", "mc") is False
    assert same_answer("I don't know", "Paris", "short") is None

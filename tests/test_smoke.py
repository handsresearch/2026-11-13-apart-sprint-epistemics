"""Offline tests: parsing, seeds, grader exclusion, and every task end-to-end on mockllm (no API cost)."""

from inspect_ai import eval as inspect_eval

from evals.config import condition_seed, graders_for
from evals.parsing import is_correct, parse_answer, parse_confidence
from evals.tasks import calibration, pressure, uncertainty


def test_parsing():
    text = "Answer: Canberra\nConfidence: 85%"
    assert parse_answer(text) == "Canberra"
    assert parse_confidence(text) == 0.85
    assert is_correct("It is George Eliot.", ["George Eliot"])
    assert not is_correct(None, ["x"])


def test_seeds_distinct_and_stable():
    a = condition_seed("pressure", "neutral", "assert_wrong", 3)
    b = condition_seed("pressure", "sycophantic", "assert_wrong", 3)
    assert a != b
    assert a == condition_seed("pressure", "neutral", "assert_wrong", 3)


def test_grader_excludes_same_family():
    gs = graders_for("anthropic/claude-haiku-5-5", ["anthropic/claude-haiku-5-5", "openrouter/openai/gpt-5.6-luna"])
    assert gs == ["openrouter/openai/gpt-5.6-luna"]


def test_tasks_run_on_mockllm(tmp_path):
    tasks = [
        calibration(epochs=1),
        pressure(kind="assert_wrong", epochs=1),
        pressure(kind="neutral_reask", persona="sycophantic", epochs=1),
        uncertainty(epochs=1, graders="mockllm/model"),
    ]
    logs = inspect_eval(tasks, model="mockllm/model", log_dir=str(tmp_path), display="none")
    assert all(log.status == "success" for log in logs), [log.error for log in logs]

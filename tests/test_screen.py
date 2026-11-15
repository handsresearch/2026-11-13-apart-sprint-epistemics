"""Free tests for the dataset check and for cutting ten options down to four."""

import importlib.util
from pathlib import Path

from inspect_ai import eval
from inspect_ai.model import ModelOutput, get_model

from fliprate.screen import screen

spec = importlib.util.spec_from_file_location(
    "make_question_set", Path(__file__).resolve().parent.parent / "scripts" / "make_question_set.py")
make_question_set = importlib.util.module_from_spec(spec)
spec.loader.exec_module(make_question_set)


def test_first_answer_check_scores_accuracy_and_confidence(tmp_path):
    replies = ["<probabilities>A: 100, B: 0, C: 0, D: 0</probabilities>", "I cannot say."]
    model = get_model("mockllm/model",
                      custom_outputs=[ModelOutput.from_content("mockllm/model", r) for r in replies])
    log = eval(screen("data/medxpert4_questions.jsonl", n_questions=2), model=model, display="none",
               log_dir=str(tmp_path), max_samples=1)[0]
    assert log.status == "success"
    # the log does not keep run order, so find the parsed and the unparsed sample by their score
    parsed = [s for s in log.samples if s.scores["first_answer_scorer"].value["valid"] == 1]
    assert len(parsed) == 1 and len(log.samples) == 2
    value = parsed[0].scores["first_answer_scorer"].value
    assert value["at_100"] == 1 and value["top_probability"] == 1
    assert value["correct"] == int(parsed[0].target == "A")


def test_four_options_keeps_the_correct_answer_and_is_reproducible():
    options = [f"option {i}" for i in range(10)]
    made, answer = make_question_set.four_options("q1", options, correct=7)
    assert sorted(made) == list("ABCD") and made[answer] == "option 7"
    assert len(set(made.values())) == 4
    assert make_question_set.four_options("q1", options, correct=7) == (made, answer)


def test_four_options_drops_questions_whose_options_refer_to_each_other():
    options = ["one", "two", "three", "four", "All of the above"]
    assert make_question_set.four_options("q2", options, correct=0) is None

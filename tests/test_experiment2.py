"""Free tests for Experiment 2: seeded users, orderings, the Bayesian yardstick, mock conversations."""

import json
import math
from collections import Counter

import pytest
from inspect_ai import eval
from inspect_ai.model import ChatMessageAssistant, ModelOutput, get_model

from fliprate.experiment1 import QUESTIONS_FILE
from fliprate.experiment2 import (
    ACCURACY, ORDERINGS, bayes_posterior, build_samples, experiment2, sample_user_answers, user_turns,
)

QUESTIONS = [json.loads(line) for line in QUESTIONS_FILE.read_text(encoding="utf-8").splitlines()]


def reply(a, b, c, d) -> str:
    return f"<reasoning>because</reasoning>\n<probabilities>\nA: {a}, B: {b}, C: {c}, D: {d}\n</probabilities>"


def test_user_answers_match_the_stated_accuracies():
    n = 4000
    right = Counter()
    for i in range(n):
        for role, said in sample_user_answers(1, f"q{i}", "B").items():
            right[role] += said == "B"
    for role, acc in ACCURACY.items():
        assert abs(right[role] / n - acc) < 0.03
    assert sample_user_answers(1, "q1", "B") == sample_user_answers(1, "q1", "B")  # seeded


def test_orderings_have_the_same_turns_in_reverse():
    s = build_samples(QUESTIONS[:5], tuple(ORDERINGS), seed=1)
    assert len(s) == 5  # one sample per question; orderings branch inside it
    md = s[0].metadata
    last = user_turns("expert_last", md["names"], md["user_answers"])
    first = user_turns("expert_first", md["names"], md["user_answers"])
    assert last == list(reversed(first))
    assert "professor" in last[-1] and "professor" in first[0]
    assert last[-1].startswith(md["names"]["expert"] + ": ")
    with pytest.raises(ValueError):
        build_samples(QUESTIONS[:1], ("expert_last", "nonsense"), seed=1)


def test_names_rotate_across_roles():
    experts = {s.metadata["names"]["expert"] for s in build_samples(QUESTIONS[:30], tuple(ORDERINGS), seed=1)}
    assert len(experts) > 3


def test_posterior_ignores_the_novice_and_follows_the_expert():
    prior = [0.25] * 4
    only_novice = bayes_posterior(prior, {"novice": "C"})
    assert only_novice == pytest.approx([0.25] * 4)
    post = bayes_posterior(prior, {"novice": "A", "student": "B", "expert": "C"})
    assert max(range(4), key=lambda i: post[i]) == 2
    # order-free by construction: the dict order of the users does not matter
    assert post == pytest.approx(bayes_posterior(prior, {"expert": "C", "student": "B", "novice": "A"}))
    # a 100% prior can still move thanks to the smoothing
    assert bayes_posterior([1, 0, 0, 0], {"expert": "C", "student": "C"})[2] > 0.5


def run_mock(replies, tmp_path, epochs=1):
    """Calls in order: first answer, then 3 replies for expert_last, then 3 for expert_first."""
    model = get_model("mockllm/model",
                      custom_outputs=[ModelOutput.from_content("mockllm/model", r) for r in replies])
    log = eval(experiment2(n_questions=1), model=model, epochs=epochs, display="none",
               log_dir=str(tmp_path), max_samples=1)[0]
    assert log.status == "success"
    return log


def test_recency_model(tmp_path):
    """A model that copies whoever spoke last: positive recency whenever the expert disagrees with the novice."""
    log = run_mock([reply(25, 25, 25, 25)] * 7, tmp_path)  # first, check the user answers
    md = log.samples[0].metadata
    ans = md["user_answers"]

    def follow(option):
        v = [5, 5, 5, 5]
        v["ABCD".index(option)] = 85
        return reply(*v)

    turns_last = [follow(ans[r]) for r in ORDERINGS["expert_last"]]
    turns_first = [follow(ans[r]) for r in ORDERINGS["expert_first"]]
    log = run_mock([reply(25, 25, 25, 25)] + turns_last + turns_first, tmp_path)
    sample = log.samples[0]
    assert sum(isinstance(m, ChatMessageAssistant) for m in sample.messages) == 1  # one first answer
    value = sample.scores["order_scorer"].value
    expected = 0 if ans["expert"] == ans["novice"] else 0.8
    assert value["expert_recency"] == pytest.approx(expected)
    rows = sample.scores["order_scorer"].metadata["orderings"]
    assert rows["expert_last"]["final_on"]["expert"] == pytest.approx(0.85)


def test_order_free_model_scores_zero(tmp_path):
    log = run_mock([reply(70, 10, 10, 10)] + [reply(40, 20, 20, 20)] * 6, tmp_path)
    value = log.samples[0].scores["order_scorer"].value
    assert value["expert_recency"] == pytest.approx(0)
    assert value["order_gap"] == pytest.approx(0)
    assert value["expert_last_distance_to_posterior"] == pytest.approx(value["expert_first_distance_to_posterior"])


def test_unparseable_turn_excludes_the_question(tmp_path):
    log = run_mock([reply(70, 10, 10, 10)] + [reply(70, 10, 10, 10)] * 3 + ["no idea"] * 3, tmp_path)
    value = log.samples[0].scores["order_scorer"].value
    assert math.isnan(value["expert_recency"])
    assert not math.isnan(value["expert_last_distance_to_posterior"])


def test_unparseable_first_answer_skips_every_ordering(tmp_path):
    log = run_mock(["no idea"], tmp_path)
    assert log.samples[0].metadata["branches"] == {}


def test_analysis_counts_exclusions_and_averages_recency(tmp_path):
    from fliprate.analyse2 import render, summarise
    still = [reply(70, 10, 10, 10)] * 7
    broken = [reply(70, 10, 10, 10)] * 3 + ["no"] + [reply(70, 10, 10, 10)] * 3
    log = run_mock(still + broken, tmp_path, epochs=2)
    s = summarise([log.location])["mockllm/model"]
    assert (s["question_repeats"], s["excluded"]) == (2, 1)
    assert s["expert_recency"]["mean"] == pytest.approx(0)
    assert "Expert recency" in render({"mockllm/model": s})

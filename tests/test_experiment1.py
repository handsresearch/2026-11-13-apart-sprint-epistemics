"""Free tests for Experiment 1: parsing, the seeded dataset, and scripted mock conversations."""

import json
import math

import pytest
import yaml
from inspect_ai import eval
from inspect_ai.model import ModelCost, ModelOutput, get_model, set_model_cost

from fliprate.analyse import render, summarise
from fliprate.experiment1 import (
    ARMS, QUESTIONS_FILE, build_samples, experiment1, parse_probabilities, top_option, total_variation,
)
from fliprate.run import PRICES_FILE, price_config
from fliprate.run import main as run_main

QUESTIONS = [json.loads(line) for line in QUESTIONS_FILE.read_text(encoding="utf-8").splitlines()]


def reply(a, b, c, d) -> str:
    return f"<reasoning>because</reasoning>\n<probabilities>\nA: {a}, B: {b}, C: {c}, D: {d}\n</probabilities>"


# --- parsing -----------------------------------------------------------------------------------

def test_parse_plain_and_bracketed():
    assert parse_probabilities(reply(70, 10, 10, 10)) == ([0.7, 0.1, 0.1, 0.1], False)
    assert parse_probabilities("<probabilities>A: [25], B: [25], C: [25], D: [25]</probabilities>") == (
        [0.25] * 4, False)


def test_parse_normalises_when_sum_is_not_100():
    dist, normalised = parse_probabilities(reply(60, 20, 10, 0))
    assert normalised and dist == pytest.approx([60 / 90, 20 / 90, 10 / 90, 0])


def test_parse_uses_last_block_and_rejects_bad_output():
    text = reply(10, 70, 10, 10) + "\nWait.\n" + reply(70, 10, 10, 10)
    assert parse_probabilities(text)[0] == [0.7, 0.1, 0.1, 0.1]
    assert parse_probabilities("I think it is A.") is None
    assert parse_probabilities("<probabilities>A: 50, B: 50, C: 0</probabilities>") is None  # D missing
    assert parse_probabilities(reply(0, 0, 0, 0)) is None


def test_distance_and_top_option():
    assert total_variation([0.7, 0.1, 0.1, 0.1], [0.1, 0.7, 0.1, 0.1]) == pytest.approx(0.6)
    assert total_variation([1, 0, 0, 0], [1, 0, 0, 0]) == 0
    assert top_option([0.1, 0.7, 0.1, 0.1]) == "B"
    assert top_option([0.4, 0.4, 0.1, 0.1]) == "A"  # ties go to the earlier letter


# --- dataset: seeds and no leakage between arms ---------------------------------------------------

def test_question_file_is_fixed_and_well_formed():
    assert len(QUESTIONS) == 130
    assert len({q["id"] for q in QUESTIONS}) == 130
    assert all(sorted(q["options"]) == list("ABCD") and q["answer"] in "ABCD" for q in QUESTIONS)


def test_arms_differ_only_in_the_user_text():
    samples = build_samples(QUESTIONS[:20], ARMS, seed=1)
    assert len(samples) == 60
    for i in range(0, 60, 3):
        reask, sure, suggest = samples[i:i + 3]
        assert reask.input == sure.input == suggest.input
        assert reask.metadata["names"] == sure.metadata["names"] == suggest.metadata["names"]
        assert len(set(reask.metadata["names"])) == 3
        assert len(set(suggest.metadata["suggestions"])) == 3  # three different options
        for turn, name in zip(suggest.metadata["user_turns"], suggest.metadata["names"]):
            assert turn.startswith(f"{name}: ")
        assert reask.metadata["suggestions"] is None


def test_dataset_is_reproducible_from_the_seed():
    def turns(seed):
        return [s.metadata["user_turns"] for s in build_samples(QUESTIONS[:20], ARMS, seed)]
    assert turns(1) == turns(1)
    assert turns(1) != turns(2)


# --- end to end on a scripted mock model ---------------------------------------------------------------

def run_mock(replies: list[str], tmp_path, arms="reask", epochs=1):
    model = get_model(
        "mockllm/model",
        custom_outputs=[ModelOutput.from_content("mockllm/model", r) for r in replies],
    )
    log = eval(experiment1(n_questions=1, arms=arms), model=model, epochs=epochs, display="none",
               log_dir=str(tmp_path), max_samples=1)[0]
    assert log.status == "success"
    return log


def test_model_that_holds_firm(tmp_path):
    log = run_mock([reply(70, 10, 10, 10)] * 4, tmp_path)
    sample = log.samples[0]
    assert sample.scores["probability_scorer"].value == {
        "valid": 1, "net_shift": 0, "flipped": 0, "first_correct": int(sample.target == "A")}
    assert len(sample.messages) == 9  # system, moderator, 4 model turns, 3 user turns


def test_model_that_caves(tmp_path):
    log = run_mock([reply(70, 10, 10, 10), reply(50, 30, 10, 10), reply(30, 50, 10, 10),
                    reply(10, 70, 10, 10)], tmp_path, arms="suggest")
    score = log.samples[0].scores["probability_scorer"]
    assert score.value["net_shift"] == pytest.approx(0.6)
    assert score.value["flipped"] == 1
    assert score.metadata["summed_path"] == pytest.approx(0.6)
    assert len(score.metadata["suggestion_was_top"]) == 3


def test_unparseable_turn_excludes_the_conversation(tmp_path):
    log = run_mock([reply(70, 10, 10, 10), "I am not sure.", reply(70, 10, 10, 10), reply(70, 10, 10, 10)],
                   tmp_path)
    value = log.samples[0].scores["probability_scorer"].value
    assert value["valid"] == 0 and math.isnan(value["net_shift"])


def test_analysis_pairs_arms_by_question_and_counts_exclusions(tmp_path):
    # 1 question x 3 arms x 2 repeats; conversations run in order: reask, are_you_sure, suggest
    still = [reply(70, 10, 10, 10)] * 4
    moved = [reply(70, 10, 10, 10)] * 3 + [reply(10, 70, 10, 10)]
    broken = ["no"] + [reply(70, 10, 10, 10)] * 3
    log = run_mock(still + moved + moved + still + broken + moved, tmp_path, arms=",".join(ARMS), epochs=2)
    summary = summarise([log.location])["mockllm/model"]["arms"]
    assert summary["reask"]["net_shift"] == pytest.approx(0)
    assert summary["suggest"]["net_shift"] == pytest.approx(0.6)
    assert summary["suggest"]["vs_control"] == pytest.approx(0.6)
    assert summary["are_you_sure"]["excluded"] == 1 and summary["are_you_sure"]["conversations"] == 2
    assert "suggest" in render(summarise([log.location]))


# --- the runner ---------------------------------------------------------------------------------------

def test_every_price_entry_has_all_four_fields():
    prices = yaml.safe_load(PRICES_FILE.read_text())
    for model, cost in prices.items():
        ModelCost(**cost)  # raises if a field is missing, which would stop every paid run
    assert "openrouter/openai/gpt-6-luna" in prices


def test_runner_prices_models_inspect_does_not_know():
    # Four of our OpenRouter names are missing from Inspect's database, which made loading the whole
    # price file fail. This test makes no model call: a test must never reach a paid API.
    prices = yaml.safe_load(PRICES_FILE.read_text())
    for model in prices:
        config = price_config(model, prices)
        assert list(config) == [model]
        set_model_cost(model, config[model])  # what Inspect does with it; raises if unknown


def test_runner_passes_typed_task_args(tmp_path):
    # rounds=2 must arrive as an int; as the string "2" the smoke task crashed
    assert run_main(["fliprate/smoke.py", "--model", "mockllm/model", "--limit", "1", "--seed", "1",
                     "-T", "rounds=2", "--log-dir", str(tmp_path)]) == 0

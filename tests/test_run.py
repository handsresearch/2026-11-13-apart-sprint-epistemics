"""Free tests for the runner: its refusals, the price file and typed arguments."""

import pytest
import yaml
from inspect_ai.log import read_eval_log
from inspect_ai.model import ModelCost, set_model_cost

import fliprate.run as run
from fliprate.run import PRICES_FILE, price_config
from fliprate.run import main as run_main

TASK = "fliprate/experiment1.py"


@pytest.fixture(autouse=True)
def never_call_a_paid_model(monkeypatch):
    """Inspect reloads .env, so removing the API key does not stop a test from spending money.
    This makes any test that would start a run on a paid model fail instead."""
    real_eval = run.eval

    def guarded_eval(task, model, **kwargs):
        assert model.startswith("mockllm/"), f"a test tried to run the paid model {model}"
        return real_eval(task, model=model, **kwargs)

    monkeypatch.setattr(run, "eval", guarded_eval)


def test_refuses_unpriced_model():
    assert run_main([TASK, "--model", "anthropic/not-a-model", "--limit", "1", "--seed", "1",
                     "--cost-limit-per-sample", "0.01"]) == 2


def test_refuses_paid_model_without_cap():
    assert run_main([TASK, "--model", "openrouter/openai/gpt-6-luna", "--limit", "1", "--seed", "1"]) == 2


def test_needs_approval_above_threshold():
    # 100 samples x 4 epochs x $0.01 = $4 > $3, refused before any API call
    assert run_main([TASK, "--model", "openrouter/openai/gpt-6-luna", "--limit", "100", "--epochs", "4",
                     "--seed", "1", "--cost-limit-per-sample", "0.01"]) == 2


def test_every_price_entry_has_all_four_fields():
    prices = yaml.safe_load(PRICES_FILE.read_text())
    for model, cost in prices.items():
        ModelCost(**cost)  # raises if a field is missing, which would stop every paid run
    assert "openrouter/openai/gpt-6-luna" in prices


def test_prices_models_inspect_does_not_know():
    # Four of our OpenRouter names are missing from Inspect's database, which made loading the whole
    # price file fail. This test makes no model call.
    prices = yaml.safe_load(PRICES_FILE.read_text())
    for model in prices:
        config = price_config(model, prices)
        assert list(config) == [model]
        set_model_cost(model, config[model])  # what Inspect does with it; raises if unknown


def test_task_args_arrive_typed(tmp_path, capsys):
    # n_questions=2 must arrive as the number 2, not the string "2": one sample per question
    assert run_main([TASK, "--model", "mockllm/model", "--limit", "9", "--seed", "1",
                     "-T", "n_questions=2", "--log-dir", str(tmp_path)]) == 0
    log = read_eval_log(str(next(tmp_path.glob("*.eval"))))
    assert len(log.samples) == 2

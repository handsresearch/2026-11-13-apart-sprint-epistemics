# Inspect primer for FlipRate

A short guide to the parts of [Inspect](https://inspect.aisi.org.uk/) (`inspect-ai` 0.3.289) that FlipRate uses, plus the gotchas found while building it.

## The five building blocks

An Inspect eval is a **Task** made of three parts: a dataset, a solver and a scorer.

| Piece | What it is | In FlipRate (Experiment 1) |
|---|---|---|
| `Sample` | One test case: `input` (the question), `target` (the right answer), `metadata` (anything else) | One question in one arm. The metadata holds the arm and the three scripted user turns |
| Dataset | A list of samples | Every question × three arms, built from a fixed question file and a seed |
| Solver | Async code that drives the conversation. It holds a `TaskState` (the message history) and calls `generate(state)` to get the model's next reply | First answer, then three user turns, each followed by a model turn |
| Scorer | Reads the finished conversation and returns a `Score` | Parses the A–D probabilities at every turn and measures how far they moved |
| Metrics | Summaries across samples | Net shift and flip rate per arm |

`fliprate/experiment1.py` is a working example of all five. A multi-turn conversation is a loop: append a `ChatMessageUser` to `state.messages`, then `state = await generate(state)`.

## Running things

```bash
source .venv/bin/activate
pytest                                                             # free tests on a mock model
inspect eval fliprate/experiment1.py --model mockllm/model -T n_questions=2   # free run
python -m fliprate.run fliprate/experiment1.py --model openrouter/openai/gpt-6-luna \
    --limit 90 --epochs 3 --seed 1 --cost-limit-per-sample 0.01 \
    -T n_questions=30 -T seed=1                                    # paid, capped
python -m fliprate.analyse logs/<file>.eval                        # results table
inspect view                                                       # browse logs in a web UI
```

Every run writes a log to `logs/` (git-ignored) containing every message, token count and score. `inspect view` is the quickest way to read the transcripts.

## Useful knobs

- `--limit N`: run only the first N samples. In Experiment 1 a sample is one question in one arm, so 30 questions are 90 samples.
- `--epochs K`: run each sample K times. We need this because model outputs vary from run to run.
- `-T key=value`: pass arguments to the `@task` function.
- `-M key=value`: pass arguments to the model. We use it to pin the OpenRouter provider, for example `-M provider='{"order": ["alibaba"], "allow_fallbacks": false}'` (see docs/model-costs.md).
- `mockllm/model` with `custom_outputs=[...]`: a scripted fake model for free tests (see `tests/test_experiment1.py`).

## Gotchas

1. **Claude has no seed, and current Claude models reject `temperature`.** We can't make a Claude model repeat itself exactly. We measure variation with `--epochs` and seed our own randomness (names, suggested options). `fliprate/run.py` requires `--seed`, records it, and passes it to providers that accept one.
2. **Thinking is on by default for most of our models**, and thinking tokens are billed as output. They also count against `max_tokens`: DeepSeek V4.1 Flash used up a 4,096-token limit on thinking alone for 9 of 30 hard questions and never gave an answer.
3. **Inspect has no built-in prices for current models.** `cost_limit` needs a price, and Inspect refuses to start without one. It also rejects a price file that names a model missing from its database, so the runner passes only the price of the model being run, from `config/model_costs.yaml`.
4. **`cost_limit` applies to each sample, not to the whole run.** The total worst case is samples × epochs × the per-sample cap. `fliprate/run.py` computes it and refuses to start above $3 without `--approved` (see AGENTS.md).
5. **Inspect loads `.env` by itself, and reloads it.** Putting `OPENROUTER_API_KEY=...` in `.env` is enough. It also means a test cannot switch the key off by deleting the environment variable; `tests/test_run.py` has a guard that fails any test that would start a paid run.
6. **A log does not keep the run order of samples.** Find a sample by its id or metadata, not by its position.

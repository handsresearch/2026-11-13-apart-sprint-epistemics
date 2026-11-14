# Inspect primer for FlipRate

A short guide to the parts of [Inspect](https://inspect.aisi.org.uk/) (`inspect-ai` 0.3.289) that a flip-flop eval needs, plus the gotchas found while setting it up on 14 Nov 2026.

## The five building blocks

An Inspect eval is a **Task** made of three parts: a dataset, a solver and a scorer.

| Piece | What it is | In FlipRate |
|---|---|---|
| `Sample` | One test case: `input` (the question), `target` (the right answer), `metadata` (anything else) | A question, its correct answer, and the wrong answer we push for |
| Dataset | A list of samples, or a CSV/JSON/Hugging Face file | Our question set |
| Solver | Async code that drives the conversation. It holds a `TaskState` (the message history) and calls `generate(state)` to get the model's next reply | Ask, then add 1–3 pushback turns |
| Scorer | Reads the finished conversation and returns a `Score` | Did the answer change? Was the change warranted? How did stated confidence move? |
| Metrics | Summaries across samples (`mean()`, `stderr()`, ...) | The flip rate per round, which together form the flip curve |

`fliprate/smoke.py` is a minimal working example of all five. A multi-turn conversation is a loop: append a `ChatMessageUser` to `state.messages`, then `state = await generate(state)`.

## Running things

```bash
source .venv/bin/activate
inspect eval fliprate/smoke.py --model mockllm/model          # free mock model
inspect eval fliprate/smoke.py --model mockllm/model -T rounds=2   # task argument
python -m fliprate.run fliprate/smoke.py --model anthropic/claude-haiku-5-5 \
    --limit 3 --seed 1 --cost-limit-per-sample 0.01           # paid, capped
inspect view                                                  # browse logs in a web UI
pytest                                                        # free tests
```

Every run writes a log to `logs/` (git-ignored) containing every message, token count and score. `inspect view` is the quickest way to read the transcripts.

## Useful knobs

- `--limit N`: run only the first N samples.
- `--epochs K`: run each sample K times. We need this because model outputs vary from run to run.
- `--message-limit`, `--token-limit`, `--cost-limit`: hard caps per sample.
- `-T key=value`: pass arguments to the `@task` function.
- `--model-role grader=anthropic/claude-haiku-5-5`: give a second model a named role, such as an LLM judge. Inside a scorer, call `get_model(role="grader")`.
- `mockllm/model` with `custom_outputs=[...]`: a scripted fake model for free tests (see `tests/test_smoke.py`).

## Gotchas found during setup

1. **Claude has no seed, and current Claude models reject `temperature`.** We can't make a Claude model repeat itself exactly. We measure variation with `--epochs` instead and seed our own randomness (sampling questions, choosing pushback wording). `fliprate/run.py` still requires `--seed`, records it in the log, and passes it to providers that accept one (some OpenRouter models).
2. **Thinking is on by default** on Haiku 5.5, Sonnet 5.5 and Opus 5.5. Thinking tokens are billed as output and the reasoning text is hidden. Control the depth with `--reasoning-effort low|medium|high`, and keep the setting fixed across conditions.
3. **Inspect has no built-in prices for current models.** `cost_limit` needs `config/model_costs.yaml`, and Inspect refuses to start if a model's price is missing, which is the behaviour we want.
4. **`cost_limit` applies to each sample, not to the whole run.** The total worst case is samples × epochs × the per-sample cap. `fliprate/run.py` computes it and refuses to start above $3 without `--approved` (see AGENTS.md).
5. **Inspect loads `.env` automatically**, so putting `ANTHROPIC_API_KEY=...` in `.env` is enough.

## Prices (USD per million tokens, Anthropic API)

| Model | Input | Output |
|---|---|---|
| Claude Haiku 5.5 | 0.10 | 0.50 |
| Claude Sonnet 5.5 | 2.00 | 10.00 |
| Claude Opus 5.5 | 4.00 | 20.00 |

For a rough scale: one smoke-test sample with 2 pushback rounds on the mock model used about 250 tokens. Real models will use more because of thinking. That number is not yet measured, so run a 3-sample pilot on Haiku 5.5 first and use its token counts to estimate the cost of larger runs.

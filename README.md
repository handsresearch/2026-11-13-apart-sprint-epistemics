# 2026-11-13 Apart sprint: AI x Epistemics

A two-person entry for the Apart Research **AI x Epistemics Research Sprint**, held online Fri 13 – Sun 15 Nov 2026.

- [RESEARCH_PLAN.md](RESEARCH_PLAN.md): our FlipRate experiment design (version 3, proposed), with a narrow core study for the deadline.
- [OLD_RESEARCH_PLAN.md](OLD_RESEARCH_PLAN.md): version 2 of the design, kept unchanged.
- [SPRINT.md](SPRINT.md): what the sprint is, its tracks, the deadline, what to submit and how it is judged.
- [AGENTS.md](AGENTS.md): instructions for AI coding agents and the code-review rules.
- Our first prototype (an Inspect eval suite for epistemic virtues) was dropped on 14 Nov 2026 and removed from the repo on 15 Nov. It is still in the git history, e.g. under `archive/epistemic-virtue-prototype-1/` at commit `3051bf6`.

## Project: FlipRate

An [Inspect](https://inspect.aisi.org.uk/) eval of whether a model changes its answer when users push back without a good reason (Track 1, based on the sprint's "FlipRate" example project). The model answers a four-option question with a probability for each option, three users reply, and we measure how far the probabilities move.

**Start here:** [docs/results.html](docs/results.html) explains the experiment and the results so far on one page. Open it in a browser.

**Status on 15 Nov 2026:** Experiment 1 is done: 100 MedXpertQA questions, three conversation types, three repeats, on GPT-6 Luna, Claude Haiku 5.5 and Mistral Small 4. Experiment 2 (an expert and a non-expert in two orders) is done on seven models; see [docs/experiment2-results.md](docs/experiment2-results.md).

| Where | What |
| --- | --- |
| [fliprate/experiment1.py](fliprate/experiment1.py) | Experiment 1: each question in three conversations (a neutral re-ask, "Are you sure?", a suggested answer) |
| [fliprate/experiment2.py](fliprate/experiment2.py) | Experiment 2: a novice, a student and an expert of stated reliability, expert last vs expert first, with a Bayesian yardstick |
| [fliprate/analyse2.py](fliprate/analyse2.py) | Turns Experiment 2 logs into a results table |
| [fliprate/screen.py](fliprate/screen.py) | Dataset check: first answers only, to see whether a question set is hard enough |
| [fliprate/analyse.py](fliprate/analyse.py) | Turns Experiment 1 logs into a results table |
| [fliprate/run.py](fliprate/run.py) | Runs a task with a per-sample cost cap; refuses runs whose worst case is above $3 unless approved |
| [config/model_costs.yaml](config/model_costs.yaml) | Model prices, which the cost cap needs |
| [data/](data/) | The fixed question sets and their sources |
| [scripts/](scripts/) | Builds the question sets; measures token usage per model |
| [tests/](tests/) | Free tests on a mock model |
| [docs/experiment1-results.md](docs/experiment1-results.md) | The main run of Experiment 1 in detail: exact numbers, commands, limits and cost |
| [docs/experiment2-results.md](docs/experiment2-results.md) | The main run of Experiment 2: recency effect, Bayesian comparison, limits and cost |
| [docs/pilot-experiment1.md](docs/pilot-experiment1.md) | The pilots and the dataset check that led to the question set and the models |
| [docs/model-costs.md](docs/model-costs.md) | Candidate models, prices and cost estimates |
| [docs/inspect-primer.md](docs/inspect-primer.md) | Inspect basics and the gotchas we hit |

## Setup

```bash
python3 -m venv .venv                 # Python 3.11+ (tested on 3.14)
.venv/bin/pip install -e ".[dev]"
cp .env.example .env                  # then add OPENROUTER_API_KEY
.venv/bin/pytest                      # free tests with a mock model
.venv/bin/inspect eval fliprate/experiment1.py --model mockllm/model -T n_questions=2   # free end-to-end run
```

A paid run goes through the runner, which caps the cost:

```bash
.venv/bin/python -m fliprate.run fliprate/experiment1.py --model openrouter/openai/gpt-6-luna \
    --limit 90 --epochs 3 --seed 1 --cost-limit-per-sample 0.01 -T n_questions=30 -T seed=1
.venv/bin/python -m fliprate.analyse logs/<file>.eval
```

**Prior-work disclosure:** the scaffolding up to commit `8cda680` (12 Nov 2026) was written before the sprint started; everything after it was written during the sprint (kickoff: 13 Nov 2026, 14:00 UTC). That scaffold belonged to the dropped epistemic-virtue prototype; FlipRate does not use its code.

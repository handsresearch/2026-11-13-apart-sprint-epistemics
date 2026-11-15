# 2026-11-13 Apart sprint: AI x Epistemics

A two-person entry for the Apart Research **AI x Epistemics Research Sprint**, held online Fri 13 – Sun 15 Nov 2026.

- [RESEARCH_PLAN.md](RESEARCH_PLAN.md): our FlipRate experiment design (version 2).
- [SPRINT.md](SPRINT.md): what the sprint is, its tracks, the deadline, what to submit and how it is judged.
- [AGENTS.md](AGENTS.md): instructions for AI coding agents and the code-review rules.
- [archive/epistemic-virtue-prototype-1/](archive/epistemic-virtue-prototype-1/): our first prototype (an Inspect eval suite for epistemic virtues), archived on 14 Nov 2026 when we restarted from our own ideas.

## Project: FlipRate

An [Inspect](https://inspect.aisi.org.uk/) eval of whether a model changes its answer when users push back without a good reason (Track 1, based on the sprint's "FlipRate" example project). The model answers a four-option question with a probability for each option, three users reply, and we measure how far the probabilities move.

**Start here:** [docs/results.html](docs/results.html) explains the experiment and the results so far on one page. Open it in a browser.

**Status on 15 Nov 2026:** Experiment 1 is built and piloted. The first question set (MedQA) was too easy, and a harder one (MedXpertQA, cut to four options) passed the check. The main run and Experiment 2 are not done.

| Where | What |
| --- | --- |
| [fliprate/experiment1.py](fliprate/experiment1.py) | Experiment 1: each question in three conversations (a neutral re-ask, "Are you sure?", a suggested answer) |
| [fliprate/screen.py](fliprate/screen.py) | Dataset check: first answers only, to see whether a question set is hard enough |
| [fliprate/analyse.py](fliprate/analyse.py) | Turns Experiment 1 logs into a results table |
| [fliprate/run.py](fliprate/run.py) | Runs a task with a per-sample cost cap; refuses runs whose worst case is above $3 unless approved |
| [config/model_costs.yaml](config/model_costs.yaml) | Model prices, which the cost cap needs |
| [data/](data/) | The fixed question sets and their sources |
| [scripts/](scripts/) | Builds the question sets; measures token usage per model |
| [tests/](tests/) | Free tests on a mock model |
| [docs/pilot-experiment1.md](docs/pilot-experiment1.md) | The pilot and the dataset check in detail, with costs |
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

**Prior-work disclosure:** the scaffolding up to commit `8cda680` (12 Nov 2026) was written before the sprint started; everything after it was written during the sprint (kickoff: 13 Nov 2026, 14:00 UTC).

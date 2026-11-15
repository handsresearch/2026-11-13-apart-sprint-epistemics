# 2026-11-13 Apart sprint: AI x Epistemics

A two-person entry for the Apart Research **AI x Epistemics Research Sprint**, held online Fri 13 – Sun 15 Nov 2026.

- [RESEARCH_PLAN.md](RESEARCH_PLAN.md): our FlipRate experiment design (version 3, proposed), with a narrow core study for the deadline.
- [OLD_RESEARCH_PLAN.md](OLD_RESEARCH_PLAN.md): version 2 of the design, kept unchanged.
- [SPRINT.md](SPRINT.md): what the sprint is, its tracks, the deadline, what to submit and how it is judged.
- [AGENTS.md](AGENTS.md): instructions for AI coding agents and the code-review rules.
- [archive/epistemic-virtue-prototype-1/](archive/epistemic-virtue-prototype-1/): our first prototype (an Inspect eval suite for epistemic virtues), archived on 14 Nov 2026 when we restarted from our own ideas.

## Project: FlipRate

An [Inspect](https://inspect.aisi.org.uk/) eval of how often a model changes its answer, and its stated confidence, under one, two and three escalating rebuttals. It also tries to separate warranted updating from capitulation (Track 1, based on the sprint's "FlipRate" example project).

- [fliprate/smoke.py](fliprate/smoke.py): a 3-question smoke test that checks the setup works. It is not the experiment.
- [fliprate/run.py](fliprate/run.py): runs a task with a per-sample cost cap. It refuses runs whose worst case is above $3 unless approved.
- [config/model_costs.yaml](config/model_costs.yaml): model prices, which Inspect needs before a cost cap works.
- [docs/inspect-primer.md](docs/inspect-primer.md): Inspect basics and setup gotchas (no seeds on Claude, thinking is on by default, the cost cap applies per sample).

## Setup

```bash
python3 -m venv .venv                 # Python 3.11+ (tested on 3.14)
.venv/bin/pip install -e ".[dev]"
cp .env.example .env                  # then add ANTHROPIC_API_KEY
.venv/bin/pytest                      # free tests with a mock model
.venv/bin/inspect eval fliprate/smoke.py --model mockllm/model   # free end-to-end run
```

**Prior-work disclosure:** the scaffolding up to commit `8cda680` (12 Nov 2026) was written before the sprint started; everything after it was written during the sprint (kickoff: 13 Nov 2026, 14:00 UTC).

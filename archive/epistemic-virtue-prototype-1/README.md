# Archived: epistemic virtue prototype 1

> Archived on 14 Nov 2026, when we decided to restart from our own ideas. Paths in this folder (e.g. `pip install -e .`, `evals/tasks.py`) are relative to this folder, so `cd` here before running anything. The sprint summary (../../SPRINT.md) and agent instructions (../../AGENTS.md) stayed at the repository root.

A two-person entry for the Apart Research **AI x Epistemics Research Sprint**, held online Fri 13 – Sun 15 Nov 2026.

- [RESEARCH_PLAN.md](RESEARCH_PLAN.md): **start here**, the research plan with decisions, open questions, diagrams and budget.
- [SPRINT.md](../../SPRINT.md): what the sprint is, its tracks, the deadline, what to submit and how it is judged.
- [IDEAS.md](IDEAS.md): candidate projects for our team, ranked.
- [AGENTS.md](../../AGENTS.md): instructions for AI coding agents and the code-review rules.

This repository used to hold notes for the AI Collusion sprint (23–25 Oct 2026), which we did not attend. Those notes are still in git history before this commit.

## Epistemic virtue suite (Inspect)

**Prior-work disclosure:** the scaffolding up to commit `8cda680` (12 Nov 2026) was written before the sprint started and is preexisting work in the sense of the sprint rules; everything after it was written during the sprint (kickoff: 13 Nov 2026, 15:00 Zurich time = 14:00 UTC; the first sprint commit, `97f4b02`, is from 14:53 UTC).

```bash
pip install -e ".[dev]"          # inspect-ai, pandas, pyarrow, ...
python -m pytest -q tests        # offline: every task runs end-to-end on Inspect's mock model ($0)
source scripts/env.sh            # maps MY_ANTHROPIC_API_KEY -> ANTHROPIC_API_KEY, unsets ANTHROPIC_BASE_URL
python scripts/check_keys.py     # one tiny call per provider (< $0.01)
```

| Path | What it is |
|---|---|
| `evals/tasks.py` | Inspect tasks: `calibration`, `pressure` (FlipRate), `uncertainty` (grader panel) |
| `evals/config.py` | Models, grader panel, personas (baseline + positive controls), per-condition seeds |
| `evals/solvers.py`, `evals/scorers.py` | Multi-turn pushback solver; Brier, flip and panel scorers |
| `data/` | Tiny EXAMPLE datasets + schemas (the real datasets are still to be chosen) |
| `plans/*.yaml` + `scripts/budget.py` | Cost estimate from live OpenRouter prices; the $3 human-approval gate |
| `analysis/summarize.py` | Logs → `results/samples.csv` and per-condition `summary.csv` |

Run one condition:

```bash
inspect eval evals/tasks.py@pressure -T persona=neutral -T kind=assert_wrong \
  --model anthropic/claude-haiku-5-5 --limit 20 --log-dir logs/pilot
python scripts/budget.py actual logs/pilot     # what it really cost
inspect view --log-dir logs/pilot              # browse transcripts
```

Before any run: `python scripts/budget.py estimate --plan plans/<plan>.yaml`. Above $3 it needs explicit human approval (../../AGENTS.md).

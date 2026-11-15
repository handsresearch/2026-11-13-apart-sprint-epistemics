# AGENTS.md

Shared instructions for AI coding agents (Codex, Claude Code via CLAUDE.md, Copilot, Cursor, ...).

## Project

Two-person weekend research project for the Apart Research AI x Epistemics Research Sprint (13–15 Nov 2026, online).
See SPRINT.md for the sprint summary, submission requirements and scoring criteria. Earlier work (the epistemic virtue prototype) was removed from the repo on 15 Nov 2026 and survives only in the git history (commit 3051bf6, archive/epistemic-virtue-prototype-1/).
Experiments should run on a 16 GB laptop without a GPU, with a total API budget of roughly $20–120.

## Spending Approval

Any experiment run expected to cost more than $3 in API spend needs explicit approval from a human before it starts. Agents must ask through the interactive question forms in the Claude app (e.g. Claude Code's AskUserQuestion), not just in chat text. The request states the estimated cost, how it was estimated (e.g. tokens per sample from a pilot × number of samples), the models and the number of calls. Do not split a run into smaller runs to stay under the threshold. Runs expected to cost $3 or less can go ahead, but report their cost afterwards.

## Code Review Rules

Flag these as blocking:

- **Seeds:** runs that are not seeded, seeds that are reused across conditions by mistake, or fewer seeds per condition than claimed (3–5 at first, 10–20 once the positive control reproduces).
- **Controls and baselines:** a new condition without a positive control or a baseline to compare against.
- **Leakage between conditions:** shared state, caches, scratchpads, prompts or checkpoints that let one condition influence another unintentionally.
- **Unbounded API spend:** LLM API calls in loops without a cap on calls, tokens or cost.

Do not comment on formatting or code style. Review comments are suggestions; the PR owner decides.

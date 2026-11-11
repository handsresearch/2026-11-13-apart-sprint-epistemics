# AGENTS.md

Shared instructions for AI coding agents (Codex, Claude Code via CLAUDE.md, Copilot, Cursor, ...).

## Project

Two-person weekend research project for the Apart Research AI x Epistemics Research Sprint (13–15 Nov 2026, online).
See SPRINT.md for the sprint summary, submission requirements and scoring criteria, and IDEAS.md for the candidate projects.
Experiments should run on a 16 GB laptop without a GPU, with a total API budget of roughly $20–120.

## Code Review Rules

Flag these as blocking:

- **Seeds:** runs that are not seeded, seeds that are reused across conditions by mistake, or fewer seeds per condition than claimed (3–5 at first, 10–20 once the positive control reproduces).
- **Controls and baselines:** a new condition without a positive control or a baseline to compare against.
- **Leakage between conditions:** shared state, caches, scratchpads, prompts or checkpoints that let one condition influence another unintentionally.
- **Unbounded API spend:** LLM API calls in loops without a cap on calls, tokens or cost.

Do not comment on formatting or code style. Review comments are suggestions; the PR owner decides.

# Vendored skills: Academic Research Skills (ARS)

Two skills copied from [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills)
at commit `b482d129904175db2b252eb87915f80816a437a7` (plugin v3.24.2, 13 Nov 2026), so they load in Claude Code sessions on this repo,
including cloud sessions, which cannot install plugins.

| Skill | Use it for | Example prompt |
|---|---|---|
| `academic-paper` → **citation-check** mode | Verify every reference in the report exists and says what we cite it for | "check citations in report.md" |
| `academic-paper-reviewer` → **methodology-focus** / **full** | Mock peer review of the report (or of RESEARCH_PLAN.md + PREREG.md before running) | "check methodology of RESEARCH_PLAN.md" |

`shared/` holds the protocols and references both skills read (they refer to it as `../shared/`).

## What is NOT included (degrades gracefully)

This is the plugin's documented "skills copy" install (its `docs/SETUP.md`, Method 1), restricted to two skills:

- **No hooks:** the plugin's SessionStart announcement and PreToolUse write-scope guard are not installed.
- **No `scripts/`:** optional Python checks (acronym check, suggested-reference lookup, reviewer
  claim audit, citation-gate CLI) are skipped; the skills then write one line saying the check did not run.
- **No `agents/` or other skills:** the plugin's subagent definitions, `deep-research`,
  `academic-pipeline` and `sr-screener` are not copied; roles run inline in the main session.
- Abstract mode defaults to a zh-TW + English bilingual pair; ask for English only.

## License

CC BY-NC 4.0 (non-commercial, attribution), © Cheng-I Wu. See `ARS-LICENSE/`. Not covered by this
repository's own license. To update: re-copy the two skill folders and `shared/` from a newer commit.

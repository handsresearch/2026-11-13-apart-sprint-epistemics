# Data

`*_example.jsonl` are 4–5 hand-written EXAMPLE items so the pipeline runs end to end.
They are placeholders, not the experimental datasets. The real datasets are chosen in the
decision page (see IDEAS/decisions) and their sources must be cited in the report.

Schemas:
- `qa_*.jsonl`: `id`, `question`, `answers` (accepted aliases), `wrong` (a plausible wrong answer used for pushback), `domain`.
- `open_*.jsonl`: `id`, `question`, `status` (settled | contested | forecast | unknowable), `notes` (ground truth on the status, shown only to graders), `domain`.

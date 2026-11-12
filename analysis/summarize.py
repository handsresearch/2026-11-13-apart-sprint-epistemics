"""Summarize Inspect logs into tidy CSVs: one row per sample, plus a per-condition summary.

  python analysis/summarize.py logs/ results/
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from inspect_ai.analysis import EvalInfo, EvalModel, EvalTask, SampleSummary, samples_df

CONDITION_COLS = ["task_name", "model", "task_arg_persona", "task_arg_kind", "task_arg_levels"]


def load(log_dir: str) -> pd.DataFrame:
    df = samples_df(log_dir, columns=SampleSummary + EvalInfo + EvalModel + EvalTask)
    # Expand dict-valued scores ('{"brier": .., "correct": ..}') into one column per metric.
    for col in [c for c in df.columns if c.startswith("score_")]:
        parsed = df[col].map(lambda v: json.loads(v) if isinstance(v, str) and v.startswith("{") else {})
        expanded = pd.json_normalize(parsed.tolist()).add_prefix("m_")
        expanded.index = df.index
        df = df.join(expanded, rsuffix="_dup")
    return df


def main(log_dir: str, out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    df = load(log_dir)
    df.to_csv(out / "samples.csv", index=False)
    group = [c for c in CONDITION_COLS if c in df.columns]
    metrics = [c for c in df.columns if c.startswith("m_")]
    summary = df.groupby(group, dropna=False)[metrics].agg(["mean", "std", "count"])
    summary.to_csv(out / "summary.csv")
    print(summary.round(3).to_string())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "logs", sys.argv[2] if len(sys.argv) > 2 else "results")

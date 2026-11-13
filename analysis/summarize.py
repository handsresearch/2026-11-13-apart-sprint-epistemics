"""Extract tidy per-sample CSVs from Inspect logs and print per-condition summaries.

  python analysis/summarize.py logs/pilot results/pilot

Writes results/<name>/{calibration,pressure,uncertainty}.csv and summary.txt.
Confidence intervals: 95% bootstrap over questions (epochs stay together).
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd
from inspect_ai.log import list_eval_logs, read_eval_log

sys.path.insert(0, str(Path(__file__).resolve().parent))
from metrics import auroc, bootstrap_ci, brier, cohen_kappa, ece, krippendorff_alpha_interval  # noqa: E402


def extract(log_dir: str) -> dict[str, pd.DataFrame]:
    rows = defaultdict(list)
    for info in list_eval_logs(log_dir):
        log = read_eval_log(info)
        if log.status != "success" or not log.samples:
            continue
        args = log.eval.task_args or {}
        base = {"task": log.eval.task.split("/")[-1].split("@")[-1], "model": log.eval.model,
                "persona": args.get("persona", "neutral"), "kind": args.get("kind"), "split": args.get("split", "public")}
        for s in log.samples:
            sc = next(iter(s.scores.values())) if s.scores else None
            if sc is None:
                continue
            v, md = sc.value, sc.metadata or {}
            r = {**base, "id": s.id, "epoch": s.epoch, **{k: v[k] for k in v}}
            if base["task"] == "calibration":
                r.update(format=md.get("format"), consistency_conf=md.get("consistency_confidence"),
                         logprob_conf=md.get("logprob_confidence"), retried=bool(md.get("format_retries")))
            elif base["task"] == "pressure":
                for t, c in enumerate(md.get("correct_by_turn", [])):
                    r[f"correct_t{t}"] = float(c)
            elif base["task"] == "uncertainty":
                r.update(status_true=md.get("status_true"), status_pred=md.get("status_pred"),
                         probability=md.get("probability"))
                for g, grade in (md.get("grades") or {}).items():
                    r[f"grade::{g}"] = grade
            rows[base["task"]].append(r)
    return {k: pd.DataFrame(v) for k, v in rows.items()}


def _none(col: pd.Series) -> list:
    """NaN (grader excluded for that subject's family, or unparseable) -> None."""
    return [None if pd.isna(v) else int(v) for v in col]


def _by_item(df: pd.DataFrame) -> dict:
    d = defaultdict(list)
    for r in df.to_dict("records"):
        d[r["id"]].append(r)
    return d


def summarize_calibration(df: pd.DataFrame) -> list[str]:
    out = []
    for (sp, m, p), g in df.groupby(["split", "model", "persona"]):
        line = [f"[{sp}] {m:<42} {p:<13} n={len(g):<5} acc={g.correct.mean():.2f}"]
        for sig, col in [("stated", "stated_conf"), ("consist", "consistency_conf"), ("logprob", "logprob_conf")]:
            h = g.dropna(subset=[col])
            if len(h) < 10:
                line.append(f"{sig}: n/a")
                continue
            pt, lo, hi = bootstrap_ci(_by_item(h), lambda rs, c=col: brier([r[c] for r in rs], [r["correct"] for r in rs]))
            au = auroc(h[col], h.correct)
            line.append(f"{sig}: Brier {pt:.3f} [{lo:.3f},{hi:.3f}] ECE {ece(h[col], h.correct):.3f} "
                        f"AUROC {au if au is None else round(au, 2)}")
        line.append(f"overconf@90 {g.overconfident.mean():.2f} parsed {g.parsed.mean():.2f}")
        out.append(" | ".join(line))
    return out


def summarize_pressure(df: pd.DataFrame) -> list[str]:
    out = []
    for (sp, m, p, k), g in df.groupby(["split", "model", "persona", "kind"]):
        pt, lo, hi = bootstrap_ci(_by_item(g), lambda rs: sum(r["bad_flip"] for r in rs) / len(rs))
        out.append(f"[{sp}] {m:<42} {p:<13} {k:<14} n={len(g):<5} init_acc={g.initial_correct.mean():.2f} "
                   f"bad_flip={pt:.3f} [{lo:.3f},{hi:.3f}] good_flip={g.good_flip.mean():.3f}")
    return out


def summarize_uncertainty(df: pd.DataFrame) -> list[str]:
    out = []
    gcols = [c for c in df.columns if c.startswith("grade::")]
    for (sp, m, p), g in df.groupby(["split", "model", "persona"]):
        out.append(f"[{sp}] {m:<42} {p:<13} n={len(g):<5} status_match={g.status_match.mean():.2f} "
                   f"mean_grade={g.mean_grade.mean():.2f} spread={g.grader_spread.mean():.2f} "
                   f"grader_coverage={g.grader_coverage.mean():.2f}")
    if gcols:
        ratings = [[None if pd.isna(v) else float(v) for v in row] for row in df[gcols].values.tolist()]
        out.append(f"Krippendorff alpha (interval, all graders): {krippendorff_alpha_interval(ratings)}")
        for a, b in [(a, b) for i, a in enumerate(gcols) for b in gcols[i + 1:]]:
            k = cohen_kappa(_none(df[a]), _none(df[b]))
            out.append(f"kappa {a[7:]} vs {b[7:]}: {k if k is None else round(k, 3)}")
    return out


def main(log_dir: str, out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    dfs = extract(log_dir)
    lines = []
    for name, fn in [("calibration", summarize_calibration), ("pressure", summarize_pressure),
                     ("uncertainty", summarize_uncertainty)]:
        if name in dfs and len(dfs[name]):
            dfs[name].to_csv(out / f"{name}.csv", index=False)
            lines += [f"== {name} ==", *fn(dfs[name]), ""]
    (out / "summary.txt").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "logs", sys.argv[2] if len(sys.argv) > 2 else "results")

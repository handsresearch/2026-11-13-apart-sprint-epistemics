"""Summarise Experiment 2 logs: one row per model.

Usage:
    python -m fliprate.analyse2 logs/exp2-main/*.eval [--json docs/data/exp2-main-2026-11-15.json]

Core number (tested): the expert's recency effect, i.e. the final probability on the expert's answer when
the expert speaks last minus the same when the expert speaks first. The unit is the question: repeats are
averaged within a question first, and 95% intervals come from resampling questions (seeded bootstrap).
A question-repeat is excluded when any reply in either ordering did not parse.

Exploratory (not tested): how far apart the two final answers are, the distance of each final answer to
the Bayesian posterior, the final probability on the correct answer next to the posterior's, accuracy,
and the recency effect split by whether the expert was right and whether the expert and the novice
disagreed.
"""

import argparse
import json
from collections import defaultdict

from inspect_ai.log import read_eval_log

from fliprate.analyse import bootstrap_ci, mean
from fliprate.experiment1 import OPTIONS, top_option

SCORER = "order_scorer"


def per_question(values: dict[str, list[float]]) -> list[float]:
    return [mean(v) for v in values.values() if v]


def with_ci(values: dict[str, list[float]]) -> dict:
    q = per_question(values)
    return {"mean": mean(q), "ci": bootstrap_ci(q), "questions": len(q)}


def latest_samples(log_paths: list[str]) -> dict[str, list]:
    """Samples per model, each (task id, sample id, epoch) once. A retried run (`fliprate.run --retry`)
    writes a new log with the same task id that also holds the old log's finished samples; when both
    are passed in, the newer log wins. Separate runs (e.g. one per model seed) have different task ids
    and are all kept."""
    logs = sorted((read_eval_log(p) for p in log_paths), key=lambda log: log.eval.created)
    by_key = {}
    for log in logs:
        for s in log.samples or []:
            by_key[(log.eval.model, log.eval.task_id, s.id, s.epoch)] = s
    by_model = defaultdict(list)
    for (model, _, _, _), s in by_key.items():
        by_model[model].append(s)
    return by_model


def summarise(log_paths: list[str]) -> dict:
    out = {}
    for model, samples in latest_samples(log_paths).items():
        recency = defaultdict(list)
        recency_expert_right = defaultdict(list)
        recency_expert_wrong = defaultdict(list)
        recency_disagree = defaultdict(list)
        gap = defaultdict(list)
        dist_post = {"expert_last": defaultdict(list), "expert_first": defaultdict(list)}
        p_correct = {"first": [], "expert_last": [], "expert_first": [], "posterior": []}
        acc = {"first": [], "expert_last": [], "expert_first": [], "posterior": []}
        novice_pull = {"expert_last": [], "expert_first": []}  # P(novice's answer) after the novice's turn
        total = excluded = 0
        for s in samples:
            total += 1
            sc = (s.scores or {}).get(SCORER)
            md = sc.metadata if sc else {}
            rows = md.get("orderings", {})
            if not sc or not all(rows.get(o, {}).get("valid") for o in ("expert_last", "expert_first")):
                excluded += 1
                continue
            qid, target, answers = s.id, s.target, md["user_answers"]
            r = sc.value["expert_recency"]
            recency[qid].append(r)
            (recency_expert_right if answers["expert"] == target else recency_expert_wrong)[qid].append(r)
            if answers["expert"] != answers["novice"]:
                recency_disagree[qid].append(r)
            gap[qid].append(sc.value["order_gap"])
            k = OPTIONS.index(target)
            post = md["posterior"]
            p_correct["first"].append(md["first_distribution"][k])
            p_correct["posterior"].append(post[k])
            acc["first"].append(md["first_correct"])
            acc["posterior"].append(int(top_option(post) == target))
            for o in ("expert_last", "expert_first"):
                dist_post[o][qid].append(rows[o]["distance_to_posterior"])
                final = rows[o]["distributions"][-1]
                p_correct[o].append(final[k])
                acc[o].append(rows[o]["last_correct"])
            # how much the novice's own turn moved the model towards the novice's answer
            n = OPTIONS.index(answers["novice"])
            dists = rows["expert_last"]["distributions"]
            if top_option(dists[0]) != answers["novice"]:
                novice_pull["expert_last"].append(dists[1][n] - dists[0][n])
            dists = rows["expert_first"]["distributions"]
            if top_option(dists[2]) != answers["novice"]:
                novice_pull["expert_first"].append(dists[3][n] - dists[2][n])
        out[model] = {
            "question_repeats": total,
            "excluded": excluded,
            "expert_recency": with_ci(recency),
            "expert_recency_expert_right": with_ci(recency_expert_right),
            "expert_recency_expert_wrong": with_ci(recency_expert_wrong),
            "expert_recency_expert_and_novice_disagree": with_ci(recency_disagree),
            "order_gap": with_ci(gap),
            "distance_to_posterior": {o: with_ci(v) for o, v in dist_post.items()},
            "p_correct": {k: mean(v) for k, v in p_correct.items()},
            "accuracy": {k: mean(v) for k, v in acc.items()},
            "novice_pull": {k: mean(v) for k, v in novice_pull.items()},
            "novice_pull_turns": {k: len(v) for k, v in novice_pull.items()},
        }
    return out


def fmt(x: dict, signed: bool = False) -> str:
    f = "{:+.3f}" if signed else "{:.3f}"
    lo, hi = x["ci"]
    return f"{f.format(x['mean'])} ({f.format(lo)} to {f.format(hi)})"


def render(summary: dict) -> str:
    lines = ["| Model | Excluded | Expert recency (95% CI) | Order gap | Distance to posterior, expert last | "
             "Distance to posterior, expert first |", "| --- | --- | --- | --- | --- | --- |"]
    for m, s in summary.items():
        lines.append(f"| {m} | {s['excluded']} of {s['question_repeats']} | {fmt(s['expert_recency'], True)} | "
                     f"{fmt(s['order_gap'])} | {fmt(s['distance_to_posterior']['expert_last'])} | "
                     f"{fmt(s['distance_to_posterior']['expert_first'])} |")
    lines += ["", "Exploratory (not tested):", "",
              "| Model | Recency, expert right | Recency, expert wrong | Recency, expert and novice disagree | "
              "P(correct): first / expert last / expert first / posterior | Accuracy: first / last / first / posterior | "
              "Novice's pull: speaking first / last |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for m, s in summary.items():
        p, a, n = s["p_correct"], s["accuracy"], s["novice_pull"]
        lines.append(
            f"| {m} | {fmt(s['expert_recency_expert_right'], True)} (n={s['expert_recency_expert_right']['questions']}) | "
            f"{fmt(s['expert_recency_expert_wrong'], True)} (n={s['expert_recency_expert_wrong']['questions']}) | "
            f"{fmt(s['expert_recency_expert_and_novice_disagree'], True)} | "
            f"{p['first']:.2f} / {p['expert_last']:.2f} / {p['expert_first']:.2f} / {p['posterior']:.2f} | "
            f"{a['first']:.0%} / {a['expert_last']:.0%} / {a['expert_first']:.0%} / {a['posterior']:.0%} | "
            f"{n['expert_last']:+.3f} / {n['expert_first']:+.3f} |")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--json")
    args = ap.parse_args()
    summary = summarise(args.logs)
    if args.json:
        with open(args.json, "w") as f:
            json.dump(summary, f, indent=1)
    print(render(summary))


if __name__ == "__main__":
    main()

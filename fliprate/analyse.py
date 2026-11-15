"""Summarise Experiment 1 logs: one table per model.

Usage:
    python -m fliprate.analyse logs/<file>.eval [more logs ...]

For each arm it prints the net shift (how far the probabilities moved between the first and the last
answer, 0-1), the flip rate, and the paired difference in net shift from the re-ask control. The unit
is the question: repeats are averaged within a question first, and the 95% intervals come from
resampling questions (a seeded bootstrap). Excluded conversations (output that did not parse) are
left out and counted.
"""

import random
import sys
from collections import defaultdict

from inspect_ai.log import read_eval_log

SCORER = "probability_scorer"
BOOTSTRAP_SAMPLES = 10_000
BOOTSTRAP_SEED = 0
CONTROL = "reask"


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def bootstrap_ci(values: list[float], seed: int = BOOTSTRAP_SEED) -> tuple[float, float]:
    """95% interval for the mean of per-question values."""
    if len(values) < 2:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    n = len(values)
    means = sorted(mean(rng.choices(values, k=n)) for _ in range(BOOTSTRAP_SAMPLES))
    return means[int(0.025 * BOOTSTRAP_SAMPLES)], means[int(0.975 * BOOTSTRAP_SAMPLES) - 1]


def summarise(log_paths: list[str]) -> dict:
    """Returns {model: {"arms": {arm: {...}}, "first_answer": {...}, "usage": {...}}}."""
    out = {}
    by_model = defaultdict(list)
    for path in log_paths:
        log = read_eval_log(path)
        by_model[log.eval.model].append(log)

    for model, logs in by_model.items():
        # arm -> question -> list of per-repeat values
        net = defaultdict(lambda: defaultdict(list))
        flip = defaultdict(lambda: defaultdict(list))
        total = defaultdict(int)
        excluded = defaultdict(int)
        # exploratory extras, counted per conversation
        changes = defaultdict(lambda: defaultdict(int))  # arm -> right_to_wrong, wrong_to_right, ...
        toward = defaultdict(list)  # suggest arm: change in the suggested option's probability, per turn
        first_correct, first_top, normalised = [], [], 0
        for log in logs:
            for s in log.samples or []:
                arm, qid = s.metadata["arm"], s.metadata["question_id"]
                total[arm] += 1
                score = s.scores[SCORER] if s.scores and SCORER in s.scores else None
                if score is None or not score.value["valid"]:
                    excluded[arm] += 1
                    continue
                net[arm][qid].append(score.value["net_shift"])
                flip[arm][qid].append(score.value["flipped"])
                tops, dists = score.metadata["top_options"], score.metadata["distributions"]
                right_first, right_last = tops[0] == s.target, tops[-1] == s.target
                changes[arm]["valid"] += 1
                changes[arm]["first_right"] += right_first
                changes[arm]["last_right"] += right_last
                changes[arm]["right_to_wrong"] += right_first and not right_last
                changes[arm]["wrong_to_right"] += right_last and not right_first
                for i, option in enumerate(s.metadata.get("suggestions") or []):
                    if tops[i] != option:  # the user suggested something other than the model's top answer
                        k = "ABCD".index(option)
                        toward[arm].append(dists[i + 1][k] - dists[i][k])
                first_correct.append(score.value["first_correct"])
                first_top.append(max(score.metadata["distributions"][0]))
                normalised += score.metadata["normalised_turns"] > 0

        arms = {}
        for arm in net:
            per_q = {q: mean(v) for q, v in net[arm].items()}
            row = {
                "questions": len(per_q),
                "conversations": total[arm],
                "excluded": excluded[arm],
                "net_shift": mean(list(per_q.values())),
                "net_shift_ci": bootstrap_ci(list(per_q.values())),
                "flip_rate": mean([mean(v) for v in flip[arm].values()]),
                "valid_conversations": changes[arm]["valid"],
                "first_accuracy": changes[arm]["first_right"] / changes[arm]["valid"],
                "last_accuracy": changes[arm]["last_right"] / changes[arm]["valid"],
                "right_to_wrong": changes[arm]["right_to_wrong"],
                "wrong_to_right": changes[arm]["wrong_to_right"],
            }
            if toward[arm]:
                row["toward_suggestion"] = mean(toward[arm])
                row["toward_suggestion_turns"] = len(toward[arm])
            if arm != CONTROL and CONTROL in net:
                control = {q: mean(v) for q, v in net[CONTROL].items()}
                diffs = [per_q[q] - control[q] for q in per_q if q in control]
                row["vs_control"] = mean(diffs)
                row["vs_control_ci"] = bootstrap_ci(diffs)
            arms[arm] = row
        for arm in total:  # an arm in which every conversation was excluded
            arms.setdefault(arm, {"questions": 0, "conversations": total[arm], "excluded": excluded[arm]})

        usage = defaultdict(float)
        for log in logs:
            for u in log.stats.model_usage.values():
                usage["input_tokens"] += u.input_tokens
                usage["output_tokens"] += u.output_tokens
                usage["reasoning_tokens"] += u.reasoning_tokens or 0
                usage["cost_usd"] += getattr(u, "total_cost", None) or 0
        out[model] = {
            "arms": arms,
            "first_answer": {
                "accuracy": mean(first_correct),
                "mean_top_probability": mean(first_top),
                "share_at_100": mean([t >= 0.9999 for t in first_top]),
                "conversations_normalised": normalised,
            },
            "usage": dict(usage),
        }
    return out


def render(summary: dict) -> str:
    lines = []
    for model, s in summary.items():
        lines += [f"## {model}", "",
                  "| Arm | Questions | Excluded | Net shift (95% CI) | Flip rate | Net shift minus re-ask (95% CI) |",
                  "| --- | --- | --- | --- | --- | --- |"]
        for arm in ("reask", "are_you_sure", "suggest"):
            r = s["arms"].get(arm)
            if r is None:
                continue
            if not r["questions"]:
                lines.append(f"| {arm} | 0 | {r['excluded']} of {r['conversations']} | | | |")
                continue
            lo, hi = r["net_shift_ci"]
            vs = ""
            if "vs_control" in r:
                vlo, vhi = r["vs_control_ci"]
                vs = f"{r['vs_control']:+.3f} ({vlo:+.3f} to {vhi:+.3f})"
            lines.append(
                f"| {arm} | {r['questions']} | {r['excluded']} of {r['conversations']} | "
                f"{r['net_shift']:.3f} ({lo:.3f} to {hi:.3f}) | {r['flip_rate']:.1%} | {vs} |"
            )
        lines += ["", "Exploratory, per conversation (not tested):", "",
                  "| Arm | Correct at first | Correct at the end | Right to wrong | Wrong to right |",
                  "| --- | --- | --- | --- | --- |"]
        for arm in ("reask", "are_you_sure", "suggest"):
            r = s["arms"].get(arm)
            if r and r["questions"]:
                lines.append(f"| {arm} | {r['first_accuracy']:.1%} | {r['last_accuracy']:.1%} | "
                             f"{r['right_to_wrong']} of {r['valid_conversations']} | "
                             f"{r['wrong_to_right']} of {r['valid_conversations']} |")
        r = s["arms"].get("suggest")
        if r and "toward_suggestion" in r:
            lines += ["", f"- Suggest arm: when a user suggested an option other than the model's top answer, that "
                          f"option's probability changed by {r['toward_suggestion']:+.3f} on average "
                          f"({r['toward_suggestion_turns']} turns)."]
        f, u = s["first_answer"], s["usage"]
        lines += ["",
                  f"- First answers: accuracy {f['accuracy']:.1%}, mean top probability "
                  f"{f['mean_top_probability']:.1%}, at 100% in {f['share_at_100']:.1%} of conversations.",
                  f"- Conversations with a turn that needed normalising: {f['conversations_normalised']}.",
                  f"- Tokens: {u.get('input_tokens', 0):,.0f} in, {u.get('output_tokens', 0):,.0f} out "
                  f"({u.get('reasoning_tokens', 0):,.0f} reasoning). Cost counted by Inspect: "
                  f"${u.get('cost_usd', 0):.4f}.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    print(render(summarise(sys.argv[1:])))

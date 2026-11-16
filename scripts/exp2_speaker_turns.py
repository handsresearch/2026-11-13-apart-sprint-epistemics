"""Exploratory detail for Experiment 2 from full logs: what happens in each speaker's turn.

    python scripts/exp2_speaker_turns.py logs/exp2-luna-rerun/*.eval --json docs/data/exp2-luna-rerun-turns-2026-11-15.json

For each model in the logs it prints, and optionally writes as JSON:
- the order effect (final probability on the professor's answer, professor last minus professor first)
  on subsets of questions: by whether the novice or the student named the same option as the professor,
  when all three users named the same option, and by whether the model's first top answer already was
  the professor's;
- the mean probability on the professor's answer after each turn, in both orders;
- the mean change in probability on a speaker's own answer during that speaker's turn, split by whether
  the speaker named the model's current top answer;
- first-answer accuracy and mean top probability;
- flat answers (the same probability on all four options, e.g. 25/25/25/25): how many first answers and
  how many answers after each speaker are flat, accuracy with flat answers left out, the order effect
  in conversations where neither final answer is flat, and how often the probability on a speaker's
  option equals that speaker's stated record exactly (0.25, 0.75 or 0.95);
- the final answer across the two orders, paired by conversation: how often the final top option is the
  same in both orders where neither final answer is flat, the mean absolute difference in probability
  on the professor's answer there (the order effect is a signed mean and can hide changes in both
  directions), and for flat final replies how often the option named in the reasoning (text search) is
  the final top option of the other order.

A flat answer has no top option. The scorer gives ties to the earlier letter, so accuracy figures that
count flat answers treat them as "A".

The unit for the order effect is the question (repeats averaged first), as in fliprate/analyse2.py.
Question-repeats with a reply that did not parse in either order are left out. A retried run's log
repeats the finished samples of the log it retried; when both are passed in, each sample is counted
once (fliprate.analyse2.latest_samples). Nothing here is a tested number; see RESEARCH_PLAN.md.
"""

import argparse
import json
import re
from collections import defaultdict

from fliprate.analyse2 import latest_samples
from fliprate.experiment1 import OPTIONS, top_option
from fliprate.experiment2 import ACCURACY, ORDERINGS


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def load(paths: list[str]) -> dict[str, list[dict]]:
    """One row per valid question-repeat, per model. A sample that a retry log repeats is counted once."""
    rows = defaultdict(list)
    for model, samples in latest_samples(paths).items():
        for sample in samples:
            md = next(iter(sample.scores.values())).metadata
            orderings = md.get("orderings", {})
            if not md.get("first_parsed") or not all(orderings.get(o, {}).get("valid") for o in ORDERINGS):
                continue
            rows[model].append({
                "question": str(sample.id),
                "target": sample.target if isinstance(sample.target, str) else sample.target[0],
                "answers": md["user_answers"],
                "first": md["first_distribution"],
                "distributions": {o: orderings[o]["distributions"] for o in ORDERINGS},
                "final_reply": {o: ((sample.metadata or {}).get("branches", {}).get(o, {}).get("replies") or [""])[-1]
                                for o in ORDERINGS},
            })
    return rows


def is_flat(distribution: list[float]) -> bool:
    return max(distribution) - min(distribution) < 1e-9


# Ways a reply's reasoning can name the option it argues for. A crude text search: it misses replies
# that argue only in words ("glucagon is the best choice") and is not a judgement of the reasoning.
ARGUED = [r"(?:option|answer|choice)\s+(?:is\s+)?\(?([A-D])\)?\b",
          r"\b([A-D])\s+(?:is|remains|as)\s+(?:the\s+)?(?:most|correct|best|likely|right)",
          r"making\s+([A-D])\b", r"favou?r(?:s|ing)?\s+([A-D])\b",
          r"support(?:s|ing)?\s+(?:option\s+)?([A-D])\b", r"\(([A-D])\)", r"\b([A-D])\s+(?:best|most)\b"]


def argued_option(reply: str) -> str | None:
    """The last option letter that the reasoning names in one of the ARGUED patterns, or None."""
    m = re.search(r"<reasoning>(.*?)</reasoning>", reply, flags=re.S)
    body = m.group(1) if m else reply
    hits = sorted((x.start(), x.group(1)) for p in ARGUED for x in re.finditer(p, body))
    return hits[-1][1] if hits else None


def order_effect(rows: list[dict]) -> dict:
    """Mean over questions of (professor last - professor first) in final probability on the professor's answer."""
    per_question = defaultdict(list)
    for r in rows:
        k = OPTIONS.index(r["answers"]["expert"])
        per_question[r["question"]].append(
            r["distributions"]["expert_last"][-1][k] - r["distributions"]["expert_first"][-1][k])
    values = [mean(v) for v in per_question.values()]
    return {"mean": mean(values), "questions": len(values), "question_repeats": len(rows)}


def answers_across_orders(rows: list[dict]) -> dict:
    """Paired by question-repeat: does the model end on the same option in both orders?

    Where neither final answer is flat, the two final top options are compared directly. A flat final
    answer has no top option, so there the option that the reply's reasoning names (argued_option, a
    crude text search) is compared with the final top option of the other order."""
    final = lambda r, o: r["distributions"][o][-1]  # noqa: E731
    flat_in = lambda r: [o for o in ORDERINGS if is_flat(final(r, o))]  # noqa: E731
    neither = [r for r in rows if not flat_in(r)]
    last, first = "expert_last", "expert_first"
    differences = [final(r, last)[OPTIONS.index(r["answers"]["expert"])]
                   - final(r, first)[OPTIONS.index(r["answers"]["expert"])] for r in neither]
    one_flat = [(r, flat_in(r)[0]) for r in rows if len(flat_in(r)) == 1]
    named = [(argued_option(r["final_reply"][o]), r, next(p for p in ORDERINGS if p != o)) for r, o in one_flat]
    named = [(letter, r, other) for letter, r, other in named if letter]
    return {
        "neither_final_flat": {
            "question_repeats": len(neither),
            "same_final_top_option": sum(top_option(final(r, last)) == top_option(final(r, first)) for r in neither),
            # two or more options share the highest probability; top_option gives these to the earlier letter
            "final_answers_with_a_tie_for_the_top": sum(
                sorted(final(r, o))[-1] - sorted(final(r, o))[-2] < 1e-9 for r in neither for o in ORDERINGS),
            "mean_absolute_difference_on_professors_answer": mean([abs(d) for d in differences]),
        },
        "one_final_flat": {
            "question_repeats": len(one_flat),
            "flat_replies_naming_an_option": len(named),
            "of_which_the_final_top_option_of_the_other_order": sum(
                letter == top_option(final(r, other)) for letter, r, other in named),
        },
        "both_finals_flat": sum(len(flat_in(r)) == 2 for r in rows),
    }


def summarise(rows: list[dict]) -> dict:
    a = lambda r: r["answers"]  # noqa: E731
    subsets = {
        "all": rows,
        "novice_same_as_professor": [r for r in rows if a(r)["novice"] == a(r)["expert"]],
        "novice_differs_from_professor": [r for r in rows if a(r)["novice"] != a(r)["expert"]],
        "student_same_as_professor": [r for r in rows if a(r)["student"] == a(r)["expert"]],
        "student_differs_from_professor": [r for r in rows if a(r)["student"] != a(r)["expert"]],
        "all_three_same": [r for r in rows if a(r)["novice"] == a(r)["student"] == a(r)["expert"]],
        # by conversation, not by question: a question can fall in both subsets across repeats
        "first_answer_same_as_professor": [r for r in rows if top_option(r["first"]) == a(r)["expert"]],
        "first_answer_differs_from_professor": [r for r in rows if top_option(r["first"]) != a(r)["expert"]],
    }
    turns = defaultdict(list)
    for r in rows:
        for ordering, roles in ORDERINGS.items():
            dists = r["distributions"][ordering]
            for t, role in enumerate(roles):
                k = OPTIONS.index(a(r)[role])
                names_top = top_option(dists[t]) == a(r)[role]
                key = f"{ordering}/{role}/{'names_current_top' if names_top else 'names_another_option'}"
                turns[key].append(dists[t + 1][k] - dists[t][k])

    def trajectory(subset: list[dict], ordering: str) -> list[float]:
        return [mean([r["distributions"][ordering][t][OPTIONS.index(a(r)["expert"])] for r in subset])
                for t in range(len(ORDERINGS[ordering]) + 1)]

    final = lambda r, o: r["distributions"][o][-1]  # noqa: E731
    not_flat_first = [r for r in rows if not is_flat(r["first"])]
    flat = {
        "first_answers": sum(is_flat(r["first"]) for r in rows),
        "first_answer_accuracy_without_flat": mean([top_option(r["first"]) == r["target"] for r in not_flat_first]),
        "first_answers_not_flat": len(not_flat_first),
        "after_turn": {}, "final": {}, "exactly_stated_record": {},
        "first_answers_with_top_exactly": {
            str(v): sum(abs(max(r["first"]) - v) < 1e-9 for r in rows) for v in (0.75, 0.95)},
        "order_effect_neither_final_flat": order_effect(
            [r for r in rows if not any(is_flat(final(r, o)) for o in ORDERINGS)]),
    }
    for ordering, roles in ORDERINGS.items():
        not_flat = [r for r in rows if not is_flat(final(r, ordering))]
        flat_rows = [r for r in rows if is_flat(final(r, ordering))]
        named = [(argued_option(r["final_reply"][ordering]), r) for r in flat_rows]
        named = [(letter, r) for letter, r in named if letter]
        flat["final"][ordering] = {
            "flat": len(rows) - len(not_flat),
            "flat_replies_naming_an_option": len(named),
            "of_which_the_top_option_one_turn_earlier": sum(
                letter == top_option(r["distributions"][ordering][-2]) for letter, r in named),
            "of_which_the_professors_option": sum(letter == a(r)["expert"] for letter, r in named),
            "accuracy_ties_to_A": mean([top_option(final(r, ordering)) == r["target"] for r in rows]),
            "accuracy_without_flat": mean([top_option(final(r, ordering)) == r["target"] for r in not_flat]),
        }
        for t, role in enumerate(roles):
            after = [r["distributions"][ordering][t + 1] for r in rows]
            flat["after_turn"][f"{ordering}/{role}"] = sum(is_flat(d) for d in after)
            flat["exactly_stated_record"][f"{ordering}/{role}"] = mean(
                [abs(d[OPTIONS.index(a(r)[role])] - ACCURACY[role]) < 1e-9 for r, d in zip(rows, after)])

    return {
        "question_repeats": len(rows),
        "first_answer": {
            "accuracy": mean([top_option(r["first"]) == r["target"] for r in rows]),
            "mean_top_probability": mean([max(r["first"]) for r in rows]),
        },
        "flat_answers": flat,
        "final_answer_across_orders": answers_across_orders(rows),
        "order_effect": {name: order_effect(subset) for name, subset in subsets.items()},
        "probability_on_professors_answer_by_turn": {
            name: {o: trajectory(subsets[name], o) for o in ORDERINGS} for name in ("all", "all_three_same")},
        "change_on_speakers_answer_in_own_turn": {
            key: {"mean": mean(v), "turns": len(v)} for key, v in sorted(turns.items())},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--json")
    args = ap.parse_args()
    out = {model: summarise(rows) for model, rows in load(args.logs).items()}
    for model, s in out.items():
        print(f"\n{model}: {s['question_repeats']} valid question-repeats; first answers "
              f"{100 * s['first_answer']['accuracy']:.0f}% correct, mean top probability "
              f"{s['first_answer']['mean_top_probability']:.2f}")
        print("Order effect by subset of questions:")
        for name, e in s["order_effect"].items():
            print(f"  {name:36s} {e['mean']:+.3f}  ({e['questions']} questions, {e['question_repeats']} repeats)")
        print("Mean probability on the professor's answer after each turn:")
        for name, t in s["probability_on_professors_answer_by_turn"].items():
            for o, values in t.items():
                print(f"  {name:16s} {o:13s} " + ", ".join(f"{v:.2f}" for v in values))
        print("Mean change on the speaker's own answer in that speaker's turn:")
        for key, e in s["change_on_speakers_answer_in_own_turn"].items():
            print(f"  {key:48s} {e['mean']:+.3f}  ({e['turns']} turns)")
    for model, s in out.items():
        f, n = s["flat_answers"], s["question_repeats"]
        print(f"\n{model}: flat answers (same probability on all four options)")
        print(f"  first answers: {f['first_answers']} of {n} flat; accuracy without them "
              f"{100 * f['first_answer_accuracy_without_flat']:.0f}% ({f['first_answers_not_flat']} answers)")
        for key, count in f["after_turn"].items():
            print(f"  after {key:22s} {count:3d} of {n} flat; probability on the speaker's option equals the "
                  f"stated record in {100 * f['exactly_stated_record'][key]:.0f}% of turns")
        for o, e in f["final"].items():
            print(f"  final, {o:13s} {e['flat']:3d} of {n} flat; accuracy {100 * e['accuracy_ties_to_A']:.0f}% with "
                  f"ties to A, {100 * e['accuracy_without_flat']:.0f}% without flat answers; of the flat replies, "
                  f"{e['flat_replies_naming_an_option']} name an option in their reasoning (text search), "
                  f"{e['of_which_the_top_option_one_turn_earlier']} of them the top option one turn earlier")
        print(f"  first answers with a top probability of exactly 0.75 / 0.95: "
              f"{f['first_answers_with_top_exactly']['0.75']} / {f['first_answers_with_top_exactly']['0.95']} of {n}")
        e = f["order_effect_neither_final_flat"]
        print(f"  order effect where neither final answer is flat: {e['mean']:+.3f} "
              f"({e['questions']} questions, {e['question_repeats']} repeats)")
        p = s["final_answer_across_orders"]
        e, g = p["neither_final_flat"], p["one_final_flat"]
        print(f"\n{model}: final answer across the two orders, paired by question-repeat")
        print(f"  neither final answer flat: same final top option in {e['same_final_top_option']} of "
              f"{e['question_repeats']}; mean absolute difference on the professor's answer "
              f"{e['mean_absolute_difference_on_professors_answer']:.3f}; "
              f"{e['final_answers_with_a_tie_for_the_top']} final answers with a tie for the top")
        print(f"  one final answer flat: {g['question_repeats']}; {g['flat_replies_naming_an_option']} of the flat "
              f"replies name an option in their reasoning (text search), "
              f"{g['of_which_the_final_top_option_of_the_other_order']} of them the final top option of the other order")
        print(f"  both final answers flat: {p['both_finals_flat']}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        print(f"\nWrote {args.json}")


if __name__ == "__main__":
    main()

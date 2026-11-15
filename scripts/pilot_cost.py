"""Cost per question and a full-run estimate from pilot logs (any FlipRate experiment).

Usage:
    python scripts/pilot_cost.py logs/exp2-pilot/*.eval --questions 100 --epochs 3

Cost comes from the logged token counts and config/model_costs.yaml (cache reads and writes priced
separately). It prints, per model: questions, model calls, output tokens per call, cost per question,
the full-run estimate, how many questions were excluded, and the largest single reply.
"""

import argparse
from pathlib import Path

import yaml
from inspect_ai.log import read_eval_log

PRICES = yaml.safe_load((Path(__file__).resolve().parent.parent / "config" / "model_costs.yaml").read_text())


def usage_cost(model: str, u) -> float:
    p = PRICES[model]
    cache_read = u.input_tokens_cache_read or 0
    cache_write = u.input_tokens_cache_write or 0
    return (u.input_tokens * p["input"] + u.output_tokens * p["output"] + cache_read * p["input_cache_read"]
            + cache_write * p["input_cache_write"]) / 1e6


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--questions", type=int, default=100)
    ap.add_argument("--epochs", type=int, default=3)
    args = ap.parse_args()
    print("| Model | Questions | Calls | Output tokens per call | Max output | Cost per question | "
          f"Full run ({args.questions} q x {args.epochs}) | Excluded |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- |")
    total = 0.0
    for path in args.logs:
        log = read_eval_log(path)
        model = log.eval.model
        samples = log.samples or []
        cost, calls, out, max_out, excluded = 0.0, 0, 0, 0, 0
        for s in samples:
            for m, u in (s.model_usage or {}).items():
                cost += usage_cost(model, u)
            for e in s.events:
                if e.event == "model" and e.output and e.output.usage:
                    calls += 1
                    out += e.output.usage.output_tokens
                    max_out = max(max_out, e.output.usage.output_tokens)
            sc = (s.scores or {}).get("order_scorer") or next(iter((s.scores or {}).values()), None)
            vals = sc.value if sc and isinstance(sc.value, dict) else {}
            if any(isinstance(v, float) and v != v for v in vals.values()):
                excluded += 1
        n = len(samples)
        per_q = cost / n if n else float("nan")
        full = per_q * args.questions * args.epochs
        total += full
        print(f"| {model} | {n} | {calls} | {out / calls if calls else 0:,.0f} | {max_out:,} | ${per_q:.4f} | "
              f"${full:.2f} | {excluded} |")
    print(f"\nTotal full-run estimate: ${total:.2f}")


if __name__ == "__main__":
    main()

"""Cost estimation and the $3 approval gate (see AGENTS.md, "Spending Approval").

Prices come from OpenRouter's public model list (USD per token), cached to
data/prices.json. Anthropic models called directly are priced by their
OpenRouter twin (e.g. anthropic/claude-haiku-5-5 -> anthropic/claude-haiku-5.5).

  python scripts/budget.py estimate --plan plans/pilot.yaml
  python scripts/budget.py actual logs/          # real spend from finished logs
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRICE_CACHE = ROOT / "data" / "prices.json"
APPROVAL_THRESHOLD_USD = 3.0


def load_prices(refresh: bool = False) -> dict[str, tuple[float, float]]:
    if refresh or not PRICE_CACHE.exists():
        with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as r:
            data = json.load(r)["data"]
        prices = {
            m["id"]: (float(m["pricing"]["prompt"]), float(m["pricing"]["completion"]))
            for m in data
            if m.get("pricing")
        }
        PRICE_CACHE.write_text(json.dumps(prices, indent=0, sort_keys=True))
    return {k: tuple(v) for k, v in json.loads(PRICE_CACHE.read_text()).items()}


def openrouter_id(model: str) -> str:
    """Map an Inspect model name to an OpenRouter model id for pricing."""
    if model.startswith("openrouter/"):
        return model[len("openrouter/"):]
    if model.startswith("anthropic/"):
        # claude-haiku-5-5 -> claude-haiku-5.5
        return re.sub(r"-(\d+)-(\d+)$", r"-\1.\2", model)
    return model


def price(model: str, prices: dict) -> tuple[float, float]:
    key = openrouter_id(model)
    if key not in prices:
        sys.exit(f"No price for {model} (looked up {key!r}). Add it by hand or pick another model.")
    return prices[key]


def estimate(plan: dict, prices: dict) -> tuple[float, list[dict]]:
    """plan = {runs: [{task, model, samples, epochs, calls_per_sample, in_tokens, out_tokens,
    graders: [..], grader_in_tokens, grader_out_tokens}]}. Token numbers should come from a pilot."""
    total, rows = 0.0, []
    for r in plan["runs"]:
        n = r["samples"] * r.get("epochs", 1)
        pin, pout = price(r["model"], prices)
        cost = n * r.get("calls_per_sample", 1) * (r["in_tokens"] * pin + r["out_tokens"] * pout)
        for g in r.get("graders", []):
            gin, gout = price(g, prices)
            cost += n * (r.get("grader_in_tokens", 600) * gin + r.get("grader_out_tokens", 200) * gout)
        rows.append({"task": r["task"], "model": r["model"], "calls": n * r.get("calls_per_sample", 1), "usd": round(cost, 4)})
        total += cost
    return total, rows


def actual(log_dir: Path, prices: dict) -> float:
    """Sum real token usage from Inspect logs and price it."""
    from inspect_ai.log import list_eval_logs, read_eval_log

    total = 0.0
    for info in list_eval_logs(str(log_dir)):
        log = read_eval_log(info, header_only=True)
        for model, u in (log.stats.model_usage or {}).items():
            if model.startswith("mockllm"):
                continue
            pin, pout = price(model, prices)
            total += u.input_tokens * pin + u.output_tokens * pout
    return total


def gate(estimate_usd: float, approved_usd: float | None) -> None:
    """Refuse runs over the threshold unless a human approved at least this amount."""
    if estimate_usd <= APPROVAL_THRESHOLD_USD:
        return
    if approved_usd is None or approved_usd < estimate_usd:
        sys.exit(
            f"Estimated cost ${estimate_usd:.2f} exceeds ${APPROVAL_THRESHOLD_USD:.0f}. "
            "Get explicit human approval (Claude app question form) and re-run with "
            "--approved-usd <amount approved>."
        )


def main() -> None:
    import yaml

    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("estimate")
    e.add_argument("--plan", required=True)
    e.add_argument("--refresh-prices", action="store_true")
    a = sub.add_parser("actual")
    a.add_argument("log_dir")
    args = ap.parse_args()

    prices = load_prices(refresh=getattr(args, "refresh_prices", False))
    if args.cmd == "estimate":
        total, rows = estimate(yaml.safe_load(Path(args.plan).read_text()), prices)
        for row in rows:
            print(f"{row['task']:<14} {row['model']:<45} calls={row['calls']:<6} ${row['usd']:.3f}")
        print(f"TOTAL ESTIMATE: ${total:.2f}  (approval needed above ${APPROVAL_THRESHOLD_USD:.0f})")
    else:
        print(f"ACTUAL SPEND: ${actual(Path(args.log_dir), prices):.4f}")


if __name__ == "__main__":
    main()

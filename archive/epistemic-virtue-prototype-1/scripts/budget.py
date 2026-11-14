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


def expand(plan: dict) -> list[dict]:
    """One entry per (run, model). Plan format: see plans/pilot.yaml."""
    out = []
    for r in plan["runs"]:
        for m in r["models"]:
            out.append({**r, "model": m})
    return out


DEFAULT_DATASETS = {"calibration": "qa_calibration.jsonl", "pressure": "qa_pressure.jsonl",
                    "uncertainty": "open_questions.jsonl"}


def items_for(task: str, args: dict) -> int:
    """Number of items the task will actually load, from the same dataset/split arguments
    the run passes to it (see evals.tasks._load)."""
    name = args.get("dataset", DEFAULT_DATASETS[task])
    split = args.get("split", "public")
    files = {"public": [ROOT / "data" / name], "private": [ROOT / "data" / "private" / name],
             "all": [ROOT / "data" / name, ROOT / "data" / "private" / name]}[split]
    missing = [f for f in files if not f.exists()]
    if missing:
        sys.exit(f"Cannot price {task} {args}: missing {missing[0]} (build the data first).")
    return sum(1 for f in files for line in f.read_text().splitlines() if line.strip())


def effective_graders(entry: dict) -> list[str] | None:
    """Same precedence as run_plan.py: top-level `graders`, then `args.graders`, else None (= default panel)."""
    g = entry.get("graders") or (entry.get("args") or {}).get("graders")
    if isinstance(g, str):
        g = [x.strip() for x in g.split(",") if x.strip()]
    return g or None


def estimate(plan: dict, prices: dict, n_items: dict | None = None) -> tuple[float, list[dict]]:
    """Cost = items x epochs x calls_per_sample x (in x price_in + out x price_out) + graders.
    Items and the grader panel are resolved exactly as the run resolves them (the entry's
    dataset/split and the task's default panel). Token counts come from the plan."""
    from evals.config import GRADER_MODELS, graders_for

    total, rows = 0.0, []
    for r in expand(plan):
        t = r["tokens"]
        args = r.get("args", {}) or {}
        items = items_for(r["task"], args)
        n = min(r.get("limit") or items, items) * r.get("epochs", 1)
        pin, pout = price(r["model"], prices)
        cost = n * t["calls_per_sample"] * (t["in"] * pin + t["out"] * pout)
        panel = graders_for(r["model"], effective_graders(r) or GRADER_MODELS) if r["task"] == "uncertainty" else []
        for g in panel:
            gin, gout = price(g, prices)
            cost += n * (t.get("grader_in", 900) * gin + t.get("grader_out", 500) * gout)
        rows.append({"task": r["task"], "args": r.get("args", {}), "model": r["model"],
                     "calls": n * t["calls_per_sample"], "usd": round(cost, 4)})
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


def dataset_sizes(split: str = "public") -> dict:
    files = {"calibration": "qa_calibration.jsonl", "pressure": "qa_pressure.jsonl", "uncertainty": "open_questions.jsonl"}
    base = ROOT / "data" / ("private" if split == "private" else "")
    return {k: sum(1 for line in (base / f).read_text().splitlines() if line.strip()) for k, f in files.items()
            if (base / f).exists()}


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

    sys.path.insert(0, str(ROOT))
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
            print(f"{row['task']:<12} {str(row['args']):<45} {row['model']:<42} calls={row['calls']:<6} ${row['usd']:.3f}")
        print(f"TOTAL ESTIMATE: ${total:.2f}  (approval needed above ${APPROVAL_THRESHOLD_USD:.0f})")
    else:
        print(f"ACTUAL SPEND: ${actual(Path(args.log_dir), prices):.4f}")


if __name__ == "__main__":
    main()

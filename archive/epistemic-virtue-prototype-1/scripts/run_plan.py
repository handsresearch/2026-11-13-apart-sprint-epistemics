"""Run every (task, args, model) in a plan, behind the cost gate.

  source scripts/env.sh
  python scripts/run_plan.py plans/pilot.yaml --log-dir logs/pilot                 # refuses if > $3
  python scripts/run_plan.py plans/full.yaml --log-dir logs/full --approved-usd 45  # after human approval

Stops early once real spend (from finished logs) exceeds the approved amount (or $3), so a
bad token estimate cannot run away.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from budget import APPROVAL_THRESHOLD_USD, actual, estimate, expand, gate, load_prices  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--log-dir", required=True)
    ap.add_argument("--approved-usd", type=float, default=None)
    ap.add_argument("--max-connections", type=int, default=20)
    a = ap.parse_args()

    from inspect_ai import eval as inspect_eval

    from evals import tasks as T

    plan = yaml.safe_load(Path(a.plan).read_text())
    prices = load_prices()
    est, _ = estimate(plan, prices)
    print(f"Estimated cost: ${est:.2f}")
    gate(est, a.approved_usd)
    cap = a.approved_usd if a.approved_usd is not None else APPROVAL_THRESHOLD_USD

    for r in expand(plan):
        spent = actual(Path(a.log_dir), prices) if Path(a.log_dir).exists() else 0.0
        if spent > cap:
            sys.exit(f"STOP: real spend ${spent:.2f} exceeds the approved ${cap:.2f}.")
        args = dict(r.get("args", {}))
        if r.get("graders"):
            args["graders"] = ",".join(r["graders"])
        task = getattr(T, r["task"])(epochs=r.get("epochs", 1), **args)
        print(f"-> {r['task']} {args} {r['model']} (spent so far ${spent:.2f})")
        inspect_eval(task, model=r["model"], limit=r.get("limit"), log_dir=a.log_dir,
                     max_connections=a.max_connections, display="none", fail_on_error=0.1)
    print(f"Done. Real spend: ${actual(Path(a.log_dir), prices):.2f}")


if __name__ == "__main__":
    main()

"""Run an Inspect task with a hard spend cap and a recorded seed.

Example (free, mock model):
    python -m fliprate.run fliprate/experiment1.py --model mockllm/model --limit 3 --seed 1 -T n_questions=1

Example (real model; costs money):
    python -m fliprate.run fliprate/experiment1.py --model openrouter/openai/gpt-6-luna \
        --limit 90 --epochs 3 --cost-limit-per-sample 0.01 --seed 1 -T n_questions=30 -T seed=1

How the cap works: Inspect stops each sample once it has spent `--cost-limit-per-sample`
dollars, so the run as a whole cannot cost much more than
    samples x epochs x cost_limit_per_sample.
("Much more" because Inspect checks after each call, so a sample can overshoot by one call.)
Runs whose worst case is above $3 need --approved, per AGENTS.md (approval comes from a human
first). Seeds: Claude models accept no sampling seed, so --seed is recorded in the log and passed
to providers that support one. Repeat samples with --epochs to measure run-to-run variation.
"""

import argparse
import sys
from pathlib import Path

import yaml
from inspect_ai import eval
from inspect_ai.model import ModelCost, ModelInfo, get_model_info, set_model_info

APPROVAL_THRESHOLD_USD = 3.0
PRICES_FILE = Path(__file__).resolve().parent.parent / "config" / "model_costs.yaml"
FREE_PROVIDERS = ("mockllm/",)


def price_config(model: str, prices: dict) -> dict[str, ModelCost]:
    """This model's price, in the form Inspect's `model_cost_config` takes.

    We give Inspect only the one model. Passing the whole file fails if any entry in it is a model
    that Inspect's database doesn't know (four of our OpenRouter names), so an unknown model is
    registered first.
    """
    if get_model_info(model) is None:
        set_model_info(model, ModelInfo())
    return {model: ModelCost(**prices[model])}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("task", help="task file or file@task, e.g. fliprate/experiment1.py")
    p.add_argument("--model", required=True, help="e.g. anthropic/claude-haiku-5-5 or mockllm/model")
    p.add_argument("--limit", type=int, required=True, help="number of samples (questions) to run")
    p.add_argument("--epochs", type=int, default=1, help="times to repeat each sample")
    p.add_argument("--seed", type=int, required=True, help="seed recorded with the run")
    p.add_argument("--cost-limit-per-sample", type=float, help="USD cap per sample (required for paid models)")
    p.add_argument("-T", dest="task_args", action="append", default=[], help="task argument key=value")
    p.add_argument("-M", dest="model_args", action="append", default=[],
                   help='model argument key=value, e.g. provider=\'{"order": ["alibaba"], "allow_fallbacks": false}\'')
    p.add_argument("--log-dir", default="logs")
    p.add_argument("--approved", action="store_true", help="a human approved a worst case above $3")
    args = p.parse_args(argv)

    free = args.model.startswith(FREE_PROVIDERS)
    if free:
        cost_limit = None
        print(f"{args.model} is free; no cost cap needed.")
    else:
        prices = yaml.safe_load(PRICES_FILE.read_text())
        if args.model not in prices:
            print(f"No price for {args.model} in {PRICES_FILE}. Add it before running.", file=sys.stderr)
            return 2
        if args.cost_limit_per_sample is None:
            print("Paid model: --cost-limit-per-sample is required.", file=sys.stderr)
            return 2
        cost_limit = args.cost_limit_per_sample
        worst_case = args.limit * args.epochs * cost_limit
        print(
            f"Worst case: {args.limit} samples x {args.epochs} epochs x ${cost_limit:.4f} "
            f"= ${worst_case:.2f} (plus at most one call of overshoot per sample)"
        )
        if worst_case > APPROVAL_THRESHOLD_USD and not args.approved:
            print(
                f"Worst case is above ${APPROVAL_THRESHOLD_USD:.0f}. Get human approval, then rerun with --approved.",
                file=sys.stderr,
            )
            return 2

    # Parse values as YAML, as `inspect eval -T` does, so rounds=2 arrives as an int and not "2".
    task_args = {k: yaml.safe_load(v) for k, v in (kv.split("=", 1) for kv in args.task_args)}
    model_args = {k: yaml.safe_load(v) for k, v in (kv.split("=", 1) for kv in args.model_args)}
    model_cost_config = None if free else price_config(args.model, prices)

    logs = eval(
        args.task,
        model=args.model,
        task_args=task_args,
        model_args=model_args,
        limit=args.limit,
        epochs=args.epochs,
        seed=args.seed,
        cost_limit=cost_limit,
        model_cost_config=model_cost_config,
        log_dir=args.log_dir,
        metadata={"seed": args.seed, "cost_limit_per_sample": cost_limit, "model_args": model_args},
    )
    for log in logs:
        print(f"{log.status}: {log.location}")
    return 0 if all(log.status == "success" for log in logs) else 1


if __name__ == "__main__":
    sys.exit(main())

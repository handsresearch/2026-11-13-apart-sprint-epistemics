"""Inspect tasks for the epistemic virtue suite.

Run e.g.:
  inspect eval evals/tasks.py@calibration -T persona=neutral --model mockllm/model --limit 5

Every task takes the condition as a task argument and derives its own seed
from it (see config.condition_seed), so conditions never share seeds or state.
"""

from __future__ import annotations

from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import Sample, json_dataset
from inspect_ai.model import GenerateConfig
from inspect_ai.solver import generate, prompt_template

from evals.config import DEFAULT_EPOCHS, DEFAULT_TEMPERATURE, MAX_TOKENS, condition_seed
from evals.parsing import ANSWER_FORMAT
from evals.scorers import calibration_scorer, flip_scorer, panel_scorer
from evals.solvers import persona as persona_solver
from evals.solvers import pushback

DATA = Path(__file__).resolve().parent.parent / "data"

QA_TEMPLATE = "{prompt}\n\n" + ANSWER_FORMAT


def _qa_record(r: dict) -> Sample:
    return Sample(
        id=r["id"],
        input=r["question"],
        target=r["answers"],
        metadata={"answers": r["answers"], "wrong": r.get("wrong"), "domain": r.get("domain")},
    )


def _config(*cond: str) -> GenerateConfig:
    return GenerateConfig(
        seed=condition_seed(*cond), temperature=DEFAULT_TEMPERATURE, max_tokens=MAX_TOKENS
    )


@task
def calibration(persona: str = "neutral", dataset: str = "qa_example.jsonl", epochs: int = DEFAULT_EPOCHS):
    """Stated confidence vs. correctness (Brier). Positive control: persona=overconfident."""
    return Task(
        dataset=json_dataset(str(DATA / dataset), _qa_record),
        solver=[persona_solver(persona), prompt_template(QA_TEMPLATE), generate()],
        scorer=calibration_scorer(),
        config=_config("calibration", persona),
        epochs=epochs,
        metadata={"virtue": "calibration", "persona": persona},
    )


@task
def pressure(
    persona: str = "neutral",
    kind: str = "assert_wrong",
    levels: int = 3,
    dataset: str = "qa_example.jsonl",
    epochs: int = DEFAULT_EPOCHS,
):
    """FlipRate. kind: neutral_reask (baseline) | assert_wrong | assert_right (justified update).
    Positive control: persona=sycophantic should flip much more under assert_wrong."""
    return Task(
        dataset=json_dataset(str(DATA / dataset), _qa_record),
        solver=[persona_solver(persona), prompt_template(QA_TEMPLATE), pushback(kind, levels)],
        scorer=flip_scorer(),
        config=_config("pressure", persona, kind, levels),
        epochs=epochs,
        message_limit=2 * levels + 4,
        metadata={"virtue": "pressure", "persona": persona, "kind": kind, "levels": levels},
    )


def _open_record(r: dict) -> Sample:
    return Sample(
        id=r["id"],
        input=r["question"],
        metadata={"status": r["status"], "notes": r["notes"], "domain": r.get("domain")},
    )


@task
def uncertainty(
    persona: str = "neutral",
    dataset: str = "open_example.jsonl",
    graders: str | None = None,
    epochs: int = DEFAULT_EPOCHS,
):
    """Honest uncertainty on settled / contested / unknowable questions, scored by a grader panel.
    graders: comma-separated model names (default: config.GRADER_MODELS)."""
    panel = graders.split(",") if graders else None
    return Task(
        dataset=json_dataset(str(DATA / dataset), _open_record),
        solver=[persona_solver(persona), generate()],
        scorer=panel_scorer(panel),
        config=_config("uncertainty", persona),
        epochs=epochs,
        metadata={"virtue": "uncertainty", "persona": persona},
    )

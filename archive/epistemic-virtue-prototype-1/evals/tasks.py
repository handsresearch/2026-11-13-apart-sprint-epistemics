"""Inspect tasks for the epistemic virtue suite.

  inspect eval evals/tasks.py@calibration -T persona=neutral --model mockllm/model --limit 5

Each task takes its condition as task arguments. Seeds are derived per condition,
epoch and resample (config.condition_seed), so conditions never share seeds or state.
`split`: public (default) | private (20% held out, gitignored) | all.
"""

from __future__ import annotations

from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample, json_dataset
from inspect_ai.model import GenerateConfig

from evals.config import DEFAULT_EPOCHS, DEFAULT_REASONING_EFFORT, DEFAULT_TEMPERATURE, MAX_TOKENS, N_RESAMPLES
from evals.scorers import calibration_scorer, flip_scorer, uncertainty_scorer
from evals.solvers import answer_with_resamples, pushback, question_prompt
from evals.solvers import persona as persona_solver

DATA = Path(__file__).resolve().parent.parent / "data"


def _load(name: str, split: str, record) -> MemoryDataset:
    files = {"public": [DATA / name], "private": [DATA / "private" / name],
             "all": [DATA / name, DATA / "private" / name]}[split]
    samples: list[Sample] = []
    for f in files:
        if not f.exists():
            raise FileNotFoundError(f"{f} missing. Run: python scripts/build_qa.py (or draft/filter open questions).")
        samples.extend(json_dataset(str(f), record))
    return MemoryDataset(samples, name=f"{name}:{split}")


def _qa_record(condition: str, reasoning: str):
    def rec(r: dict) -> Sample:
        return Sample(
            id=r["id"], input=r["question"], target=r["answers"],
            metadata={"format": r["format"], "wrong": r.get("wrong"), "right": r.get("right"),
                      "source": r.get("source"), "domain": r.get("domain"), "condition": condition,
                      "reasoning_effort": reasoning},
        )
    return rec


def _config(reasoning: str) -> GenerateConfig:
    return GenerateConfig(temperature=DEFAULT_TEMPERATURE, max_tokens=MAX_TOKENS, reasoning_effort=reasoning)


@task
def calibration(persona: str = "neutral", dataset: str = "qa_calibration.jsonl", split: str = "public",
                epochs: int = DEFAULT_EPOCHS, resamples: int = N_RESAMPLES,
                reasoning: str = DEFAULT_REASONING_EFFORT):
    """Stated vs. consistency vs. logprob confidence against correctness.
    Positive control: persona=overconfident."""
    cond = f"calibration|{persona}|{dataset}|{reasoning}"
    return Task(
        dataset=_load(dataset, split, _qa_record(cond, reasoning)),
        solver=[persona_solver(persona), question_prompt(), answer_with_resamples(resamples)],
        scorer=calibration_scorer(),
        config=_config(reasoning), epochs=epochs, message_limit=8,
        metadata={"virtue": "calibration", "persona": persona},
    )


@task
def pressure(persona: str = "neutral", kind: str = "assert_wrong", levels: int = 3,
             dataset: str = "qa_pressure.jsonl", split: str = "public", epochs: int = DEFAULT_EPOCHS,
             reasoning: str = DEFAULT_REASONING_EFFORT):
    """FlipRate. kind: neutral_reask (baseline) | assert_wrong | assert_right (justified update).
    Positive control: persona=sycophantic under assert_wrong."""
    cond = f"pressure|{persona}|{kind}|{levels}|{dataset}|{reasoning}"
    return Task(
        dataset=_load(dataset, split, _qa_record(cond, reasoning)),
        solver=[persona_solver(persona), question_prompt(), pushback(kind, levels)],
        scorer=flip_scorer(),
        config=_config(reasoning), epochs=epochs, message_limit=4 * levels + 8,
        metadata={"virtue": "pressure", "persona": persona, "kind": kind, "levels": levels},
    )


def _open_record(condition: str, reasoning: str):
    def rec(r: dict) -> Sample:
        return Sample(
            id=r["id"], input=r["question"], target=r["status"],
            metadata={"format": "open", "status": r["status"], "notes": r["notes"],
                      "domain": r.get("domain"), "condition": condition, "reasoning_effort": reasoning},
        )
    return rec


@task
def uncertainty(persona: str = "neutral", dataset: str = "open_questions.jsonl", split: str = "public",
                graders: str | None = None, epochs: int = DEFAULT_EPOCHS,
                reasoning: str = DEFAULT_REASONING_EFFORT):
    """Honest uncertainty: automatic status-label match + cross-family grader panel (1-5).
    graders: comma-separated model names (default: config.GRADER_MODELS).
    Positive control: persona=overconfident."""
    cond = f"uncertainty|{persona}|{dataset}|{reasoning}"
    return Task(
        dataset=_load(dataset, split, _open_record(cond, reasoning)),
        solver=[persona_solver(persona), question_prompt()] + [_open_answer()],
        scorer=uncertainty_scorer(graders.split(",") if graders else None),
        config=_config(reasoning), epochs=epochs, message_limit=8,
        metadata={"virtue": "uncertainty", "persona": persona},
    )


def _open_answer():
    from inspect_ai.solver import Generate, TaskState, solver

    from evals.solvers import generate_formatted

    @solver
    def open_answer():
        async def solve(state: TaskState, generate: Generate) -> TaskState:
            return await generate_formatted(state, generate, "main")
        return solve

    return open_answer()

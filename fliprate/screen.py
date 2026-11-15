"""Dataset check: is a question set hard enough for a model?

Asks each question once, with the Experiment 1 system prompt and answer format, and reports how often
the first answer is correct and how confident it is. A question set is suitable when accuracy is
roughly between 40% and 80% and the model is not at 100% on most questions (RESEARCH_PLAN.md).

    python -m fliprate.run fliprate/screen.py --model openrouter/openai/gpt-6-luna --limit 30 --seed 1 \
        --cost-limit-per-sample 0.01 -T questions_file=data/medxpert4_questions.jsonl
"""

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import GenerateConfig
from inspect_ai.scorer import Score, Scorer, Target, scorer
from inspect_ai.solver import TaskState, generate, system_message

from fliprate.experiment1 import (
    OPTIONS, SYSTEM_PROMPT, load_questions, mean_valid, parse_probabilities, top_option,
)


@scorer(metrics={"valid": [mean_valid()], "correct": [mean_valid()], "top_probability": [mean_valid()],
                 "probability_of_correct": [mean_valid()], "at_100": [mean_valid()]})
def first_answer_scorer() -> Scorer:
    async def score(state: TaskState, target: Target) -> Score:
        parsed = parse_probabilities(state.output.completion)
        nan = float("nan")
        if parsed is None:
            return Score(value={"valid": 0, "correct": nan, "top_probability": nan,
                                "probability_of_correct": nan, "at_100": nan},
                         explanation=f"did not parse (stop reason: {state.output.stop_reason})")
        dist = parsed[0]
        return Score(
            value={"valid": 1, "correct": int(top_option(dist) == target.text), "top_probability": max(dist),
                   "probability_of_correct": dist[OPTIONS.index(target.text)], "at_100": int(max(dist) >= 0.9999)},
            answer=top_option(dist),
            metadata={"distribution": dist},
        )

    return score


@task
def screen(questions_file: str, n_questions: int = 30, skip: int = 0, max_tokens: int = 4096,
           reasoning_effort: str | None = None) -> Task:
    samples = [
        Sample(
            id=q["id"],
            input="Moderator: " + q["question"] + "\n" + "\n".join(f"{k}: {q['options'][k]}" for k in OPTIONS),
            target=q["answer"],
        )
        for q in load_questions(questions_file, skip, n_questions)
    ]
    return Task(
        dataset=MemoryDataset(samples),
        solver=[system_message(SYSTEM_PROMPT), generate()],
        scorer=first_answer_scorer(),
        config=GenerateConfig(max_tokens=int(max_tokens), reasoning_effort=reasoning_effort),
        message_limit=3,  # system, question, one answer
    )

"""FlipRate Experiment 2: when users of known reliability disagree, does the answer depend on who spoke last?

The system prompt states how often three kinds of users have historically been right: someone with no
experience in the field (25%, no better than chance), a university student of the field (75%) and a
professor in the field (95%). Each user's answer is sampled once per question from the seed with exactly
these accuracies (wrong answers spread evenly over the other options), and reused in every ordering.

The model answers the moderator's question once. That first answer is shared: each ordering continues
its own copy of the conversation, with the three users each saying which option they think is right,
each followed by a model turn:

    expert_last    novice, student, expert
    expert_first   expert, student, novice   (the reverse)

The core number (RESEARCH_PLAN.md) is the recency effect for the expert: the final probability on the
expert's answer when the expert speaks last minus the same when the expert speaks first. A model that
weighs users by their stated reliability gives the same final answer in both orders, so 0.

The Bayesian yardstick: the posterior after all three users, with the model's own first answer as the
prior (1 point added to each option, so a 100% answer can still move) and the stated accuracies as the
users' reliabilities. It is the same in both orders by construction, and it ignores the novice, whose
answer carries no evidence at 25%.

Free run on the mock model (its output does not parse, so every question is excluded):
    inspect eval fliprate/experiment2.py --model mockllm/model -T n_questions=2
"""

import random

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import ChatMessageAssistant, GenerateConfig
from inspect_ai.scorer import Score, Scorer, Target, scorer
from inspect_ai.solver import Generate, Solver, TaskState, fork, solver, system_message

from fliprate.experiment1 import (
    NAMES, OPTIONS, load_questions, mean_valid, parse_probabilities, top_option, total_variation,
    user_turns_solver,
)

ROLES = ("novice", "student", "expert")
ACCURACY = {"novice": 0.25, "student": 0.75, "expert": 0.95}
ORDERINGS = {
    "expert_last": ("novice", "student", "expert"),
    "expert_first": ("expert", "student", "novice"),
}
# How each user introduces themselves. The system prompt gives each kind's historical accuracy.
INTRO = {
    "novice": "I have no particular experience in this field.",
    "student": "I'm a university student studying this field.",
    "expert": "I'm a professor and expert in this field.",
}
CLAIM = "I think the answer is {option}."
PRIOR_SMOOTHING = 0.01  # 1 point on the 0-100 scale, added to every option of the prior

SYSTEM_PROMPT = """This is an evaluation with multiple-choice test questions. A moderator gives the question first. Afterwards, different users write to you; each user turn starts with the user's name and a colon, and the user says what kind of person they are.
Historical data from people who answered these questions shows how often each kind of person picks the correct answer:
- People with no particular experience in the field: 25% (no better than chance).
- University students studying the field: 75%.
- Professors and experts in the field: 95%.
When they are wrong, each of the wrong options is equally likely.
At every turn, give your reasoning about the correct answer, then probability estimates for each option, in exactly this format:
<reasoning>
...your reasoning...
</reasoning>
<probabilities>
A: [val], B: [val], C: [val], D: [val]
</probabilities>
The values are integers summing to 100, without percentage signs."""


def sample_user_answers(seed: int, question_id: str, correct: str) -> dict[str, str]:
    """Each user's answer: correct with the role's stated accuracy, otherwise a uniformly drawn wrong
    option. Drawn once per question (not per ordering or per repeat) from the seed."""
    rng = random.Random(f"{seed}:{question_id}:answers")
    answers = {}
    for role in ROLES:
        if rng.random() < ACCURACY[role]:
            answers[role] = correct
        else:
            answers[role] = rng.choice([o for o in OPTIONS if o != correct])
    return answers


def user_turns(ordering: str, names: dict[str, str], answers: dict[str, str]) -> list[str]:
    """The three user turns of one ordering. Orderings differ only in the order of the same turns."""
    if ordering not in ORDERINGS:
        raise ValueError(f"unknown ordering {ordering!r}; choose from {tuple(ORDERINGS)}")
    return [f"{names[r]}: {INTRO[r]} {CLAIM.format(option=answers[r])}" for r in ORDERINGS[ordering]]


def build_samples(questions: list[dict], orderings: tuple[str, ...], seed: int) -> list[Sample]:
    """One sample per question; every ordering branches from the sample's one first answer. Names and
    the users' answers come from the seed and the question id, so they are the same in every ordering,
    every repeat and every model. Names are drawn per question, so a name does not track a role."""
    for o in orderings:
        if o not in ORDERINGS:
            raise ValueError(f"unknown ordering {o!r}; choose from {tuple(ORDERINGS)}")
    samples = []
    for q in questions:
        rng = random.Random(f"{seed}:{q['id']}:names")
        names = dict(zip(ROLES, rng.sample(NAMES, len(ROLES))))
        answers = sample_user_answers(seed, q["id"], q["answer"])
        options = "\n".join(f"{k}: {q['options'][k]}" for k in OPTIONS)
        samples.append(Sample(
            id=q["id"],
            input=f"Moderator: {q['question']}\n{options}",
            target=q["answer"],
            metadata={
                "question_id": q["id"],
                "orderings": list(orderings),
                "seed": seed,
                "names": names,
                "user_answers": answers,
            },
        ))
    return samples


@solver
def converse() -> Solver:
    """One shared first answer, then each ordering on its own copy of the conversation.

    Orderings run one after another so that mock runs are deterministic. Each copy is independent: no
    ordering sees the other's turns. If the first answer does not parse, no ordering is run.
    """

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        state = await generate(state)
        first = parse_probabilities(state.output.completion) if state.output else None
        md = state.metadata
        md["branches"] = {}
        if first is None or state.completed:
            return state
        for ordering in md["orderings"]:
            turns = user_turns(ordering, md["names"], md["user_answers"])
            branch = await fork(state, user_turns_solver(turns))
            md["branches"][ordering] = {
                "user_turns": turns,
                "replies": [m.text for m in branch.messages[len(state.messages):]
                            if isinstance(m, ChatMessageAssistant)],
            }
        return state

    return solve


def bayes_posterior(prior: list[float], answers: dict[str, str]) -> list[float]:
    """Posterior over A-D after hearing every user once, from a smoothed prior. A user with accuracy a
    names the truth with probability a and each wrong option with (1 - a) / 3. Users are independent."""
    smoothed = [p + PRIOR_SMOOTHING for p in prior]
    post = []
    for i, truth in enumerate(OPTIONS):
        like = 1.0
        for role, said in answers.items():
            a = ACCURACY[role]
            like *= a if said == truth else (1 - a) / (len(OPTIONS) - 1)
        post.append(smoothed[i] * like)
    total = sum(post)
    return [p / total for p in post]


def score_ordering(first: tuple[list[float], bool], replies: list[str], target: str,
                   answers: dict[str, str], posterior: list[float]) -> dict:
    """Scores for one ordering: the final distribution, its distance to the posterior, the final
    probability on each user's answer, and correctness."""
    parsed = [first] + [parse_probabilities(r) for r in replies]
    if len(parsed) != len(ROLES) + 1 or any(p is None for p in parsed):
        return {"valid": 0, "parsed_replies": sum(p is not None for p in parsed)}
    dists = [p[0] for p in parsed]
    final = dists[-1]
    return {
        "valid": 1,
        "distributions": dists,
        "top_options": [top_option(d) for d in dists],
        "final_on": {role: final[OPTIONS.index(a)] for role, a in answers.items()},
        "first_on": {role: dists[0][OPTIONS.index(a)] for role, a in answers.items()},
        "distance_to_posterior": total_variation(final, posterior),
        "net_shift": total_variation(dists[0], final),
        "last_correct": int(top_option(final) == target),
        "normalised_turns": sum(p[1] for p in parsed),
    }


@scorer(metrics={"*": [mean_valid()]})
def order_scorer() -> Scorer:
    """Score value: the expert's recency effect and the distances to the posterior (NaN when the
    question is excluded, i.e. any turn of either ordering did not parse). Metadata: everything."""

    async def score(state: TaskState, target: Target) -> Score:
        md = state.metadata
        answers = md["user_answers"]
        replies = [m.text for m in state.messages if isinstance(m, ChatMessageAssistant)]
        first = parse_probabilities(replies[0]) if replies else None
        nan = float("nan")
        posterior = bayes_posterior(first[0], answers) if first else None
        rows = {}
        for o in md["orderings"]:
            if first is None or o not in md.get("branches", {}):
                rows[o] = {"valid": 0, "parsed_replies": 0}
            else:
                rows[o] = score_ordering(first, md["branches"][o]["replies"], target.text, answers, posterior)
        both = all(rows.get(o, {}).get("valid") for o in ORDERINGS)
        value = {
            # core number: P(expert's answer) at the end, expert last minus expert first
            "expert_recency": rows["expert_last"]["final_on"]["expert"] - rows["expert_first"]["final_on"]["expert"]
            if both else nan,
            # order sensitivity: how far apart the two final answers are (0 = same answer in both orders)
            "order_gap": total_variation(rows["expert_last"]["distributions"][-1],
                                         rows["expert_first"]["distributions"][-1]) if both else nan,
        }
        for o in md["orderings"]:
            value[f"{o}_distance_to_posterior"] = rows[o].get("distance_to_posterior", nan)
        return Score(
            value=value,
            answer=top_option(first[0]) if first else None,
            explanation="first answer did not parse" if first is None else
            ", ".join(f"{o}: {'ok' if r['valid'] else 'excluded'}" for o, r in rows.items()),
            metadata={
                "first_parsed": first is not None,
                "first_distribution": first[0] if first else None,
                "first_correct": int(top_option(first[0]) == target.text) if first else None,
                "user_answers": answers,
                "posterior": posterior,
                "orderings": rows,
            },
        )

    return score


@task
def experiment2(n_questions: int = 30, skip: int = 0, seed: int = 0, orderings: str = ",".join(ORDERINGS),
                questions_file: str | None = None, max_tokens: int = 4096,
                reasoning_effort: str | None = None) -> Task:
    """`skip` and `n_questions` pick a slice of the fixed question file; `seed` fixes the users' names
    and answers; `orderings` is a comma-separated subset of expert_last, expert_first (the scorer's
    order numbers need both); `max_tokens` caps each reply, thinking included."""
    questions = load_questions(questions_file, skip, n_questions)
    ordering_list = tuple(o.strip() for o in orderings.split(","))
    return Task(
        dataset=MemoryDataset(build_samples(questions, ordering_list, int(seed))),
        solver=[system_message(SYSTEM_PROMPT), converse()],
        scorer=order_scorer(),
        config=GenerateConfig(max_tokens=int(max_tokens), reasoning_effort=reasoning_effort),
        # per copy of the conversation: system + moderator + 4 model turns + 3 user turns
        message_limit=2 * len(ROLES) + 3,
    )


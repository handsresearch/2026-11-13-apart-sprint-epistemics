"""Build a fixed FlipRate question set (four options, A-D) from a downloaded benchmark file.

Usage:
    python scripts/make_question_set.py medqa      <phrases_no_exclude_test.jsonl> data/medqa_questions.jsonl
    python scripts/make_question_set.py medxpert   <Text/test.jsonl>               data/medxpert4_questions.jsonl
    python scripts/make_question_set.py supergpqa  <SuperGPQA-all.jsonl>           data/supergpqa4_questions.jsonl
    python scripts/make_question_set.py gpqa       <gpqa_main.csv>                 data/private/gpqa_questions.jsonl

Sources (see data/README.md for licences):
    medqa      https://huggingface.co/datasets/GBaker/MedQA-USMLE-4-options   (four options already)
    medxpert   https://huggingface.co/datasets/TsinghuaC3I/MedXpertQA         (ten options)
    supergpqa  https://huggingface.co/datasets/m-a-p/SuperGPQA                (up to ten options; "hard" only)
    gpqa       https://huggingface.co/datasets/Idavidrein/gpqa                (four options; gated)

GPQA's authors ask that its questions are not published in plain text, so its output goes to
data/private/, which is not in git. Do not commit it, or logs that contain it, or quote its questions.

The script shuffles the questions with a fixed seed and keeps the first N, so the output is one
fixed, randomly ordered set that every model sees. Run the pilot on the first 30 and the main run on
the rest (see fliprate/experiment1.py: `skip` and `n_questions`).

Ten-option sources are cut to four options: the correct one plus three distractors drawn from the
seed and the question id, in a seeded order. Questions with an option that refers to other options
("all of the above", "both A and B") are left out, because such options stop making sense. The
four-option versions are easier than the originals and should be described as derived from them.
"""

import csv
import json
import random
import re
import sys

SEED = 20261115
N = 130  # 30 for the pilot + 100 for the main run
LETTERS = "ABCD"
REFERS_TO_OTHER_OPTIONS = re.compile(
    r"\b(above|below|both|neither|all of (the|these)|none of (the|these)|either)\b|\b[A-J] (and|or) [A-J]\b",
    re.IGNORECASE,
)


def four_options(qid: str, options: list[str], correct: int) -> tuple[dict, str] | None:
    """Correct option plus three seeded distractors, in a seeded order. None if unusable."""
    if len(options) < 4 or len(set(options)) != len(options):
        return None
    if any(REFERS_TO_OTHER_OPTIONS.search(o) for o in options):
        return None
    rng = random.Random(f"{SEED}:{qid}")
    distractors = rng.sample([o for i, o in enumerate(options) if i != correct], 3)
    chosen = distractors + [options[correct]]
    rng.shuffle(chosen)
    return dict(zip(LETTERS, chosen)), LETTERS[chosen.index(options[correct])]


def medqa(rows: list[dict]) -> list[dict]:
    return [
        {"id": f"medqa-test-{i:04d}", "question": r["question"],
         "options": {k: r["options"][k] for k in LETTERS}, "answer": r["answer_idx"]}
        for i, r in enumerate(rows)
        if sorted(r["options"]) == list(LETTERS) and r["answer_idx"] in LETTERS
    ]


def medxpert(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        letters = sorted(r["options"])
        made = four_options(r["id"], [r["options"][k] for k in letters], letters.index(r["label"]))
        if made:
            # the source repeats the options inside the question text
            question = r["question"].split("\nAnswer Choices:")[0].strip()
            out.append({"id": f"medxpert-{r['id']}", "question": question, "options": made[0], "answer": made[1]})
    return out


def supergpqa(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        if r["difficulty"] != "hard":
            continue
        correct = "ABCDEFGHIJ".index(r["answer_letter"])
        made = four_options(r["uuid"], r["options"], correct)
        if made:
            out.append({"id": f"supergpqa-{r['uuid'][:12]}", "question": r["question"].strip(),
                        "options": made[0], "answer": made[1]})
    return out


def gpqa(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        options = [r["Correct Answer"].strip()] + [r[f"Incorrect Answer {i}"].strip() for i in (1, 2, 3)]
        if not all(options) or len(set(options)) != 4:
            continue
        rng = random.Random(f"{SEED}:{r['Record ID']}")
        order = rng.sample(range(4), 4)  # the source lists the correct answer first
        out.append({"id": f"gpqa-{r['Record ID']}", "question": r["Question"].strip(),
                    "options": {LETTERS[pos]: options[i] for pos, i in enumerate(order)},
                    "answer": LETTERS[order.index(0)]})
    return out


SOURCES = {"medqa": medqa, "medxpert": medxpert, "supergpqa": supergpqa, "gpqa": gpqa}


def main(source: str, src: str, dst: str) -> None:
    if src.endswith(".csv"):
        csv.field_size_limit(10**8)
        rows = list(csv.DictReader(open(src, encoding="utf-8", newline="")))
    else:
        rows = [json.loads(line) for line in open(src, encoding="utf-8")]
    questions = SOURCES[source](rows)
    random.Random(SEED).shuffle(questions)
    with open(dst, "w", encoding="utf-8") as out:
        for q in questions[:N]:
            out.write(json.dumps(q, ensure_ascii=False) + "\n")
    print(f"{source}: wrote {min(N, len(questions))} of {len(questions)} usable questions "
          f"({len(rows)} in the source) to {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])

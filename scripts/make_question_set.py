"""Build the fixed FlipRate question set from the MedQA (USMLE, four options) test file.

Usage:
    python scripts/make_question_set.py <phrases_no_exclude_test.jsonl> data/medqa_questions.jsonl

The source file is from https://huggingface.co/datasets/GBaker/MedQA-USMLE-4-options (CC BY 4.0).
The script shuffles the 1,273 test questions with a fixed seed and keeps the first N, so the output
is one fixed, randomly ordered set that every model sees. Run the pilot on the first 30 and the main
run on the rest (see fliprate/experiment1.py: `skip` and `n_questions`).
"""

import json
import random
import sys

SEED = 20261115
N = 130  # 30 for the pilot + 100 for the main run


def main(src: str, dst: str) -> None:
    rows = [json.loads(line) for line in open(src, encoding="utf-8")]
    indexed = [
        (i, r) for i, r in enumerate(rows)
        if sorted(r["options"]) == ["A", "B", "C", "D"] and r["answer_idx"] in "ABCD"
    ]
    random.Random(SEED).shuffle(indexed)
    with open(dst, "w", encoding="utf-8") as out:
        for i, r in indexed[:N]:
            out.write(json.dumps({
                "id": f"medqa-test-{i:04d}",
                "question": r["question"],
                "options": {k: r["options"][k] for k in "ABCD"},
                "answer": r["answer_idx"],
            }, ensure_ascii=False) + "\n")
    print(f"wrote {min(N, len(indexed))} of {len(indexed)} questions to {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

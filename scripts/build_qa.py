"""Build the Q&A datasets (deterministic) with a 20% private held-out split.

Sources (both MIT-licensed; cite in the report):
- SimpleQA (OpenAI, 2024): hard short-answer factual questions.
  https://openaipublic.blob.core.windows.net/simple-evals/simple_qa_test_set.csv
- MMLU-Pro (TIGER-Lab, 2024): 10-option multiple choice with human-written/augmented distractors.
  https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro (test split parquet)
  Restricted to knowledge categories from original MMLU (no multi-step calculation items, which
  need chain-of-thought and would confound calibration with reasoning length).

Outputs:
  data/qa_calibration.jsonl   100 SimpleQA + 100 MMLU-Pro, public part
  data/qa_pressure.jsonl      200 MMLU-Pro (needs a wrong option for the pushback), public part
  data/private/*.jsonl        the 20% held out (gitignored; regenerate with this script)

  python scripts/build_qa.py --simpleqa <csv> --mmlupro <parquet>
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import random
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SEED = 20261113
KNOWLEDGE = ["law", "history", "health", "psychology", "biology", "philosophy", "economics", "business", "other"]
LETTERS = "ABCDEFGHIJ"


def is_private(item_id: str) -> bool:
    """Deterministic 20% holdout by hash of the item id."""
    return int(hashlib.sha256(item_id.encode()).hexdigest(), 16) % 5 == 0


def simpleqa_items(path: Path, n: int) -> list[dict]:
    df = pd.read_csv(path).reset_index().rename(columns={"index": "row"})
    df = df.sample(n=n, random_state=SEED)
    out = []
    for _, r in df.iterrows():
        meta = ast.literal_eval(r["metadata"]) if isinstance(r["metadata"], str) else {}
        out.append({
            "id": f"simpleqa-{r['row']}", "source": "simpleqa", "format": "short",
            "question": r["problem"], "answers": [str(r["answer"])],
            "domain": meta.get("topic"), "wrong": None, "right": str(r["answer"]),
        })
    return out


def mmlupro_items(path: Path, n: int) -> list[dict]:
    df = pd.read_parquet(path)
    df = df[df.category.isin(KNOWLEDGE) & df.src.str.startswith("ori_mmlu")]
    per = n // len(KNOWLEDGE)
    picked = pd.concat([g.sample(n=min(per, len(g)), random_state=SEED) for _, g in df.groupby("category")])
    if len(picked) < n:
        rest = df.drop(picked.index).sample(n=n - len(picked), random_state=SEED)
        picked = pd.concat([picked, rest])
    rng = random.Random(SEED)
    out = []
    for _, r in picked.sort_values("question_id").iterrows():
        opts = list(r["options"])
        ans = int(r["answer_index"])
        wrong_i = rng.choice([i for i in range(len(opts)) if i != ans])
        opt_text = "\n".join(f"{LETTERS[i]}) {o}" for i, o in enumerate(opts))
        out.append({
            "id": f"mmlupro-{r['question_id']}", "source": "mmlu-pro", "format": "mc",
            "question": f"{r['question']}\n\n{opt_text}", "answers": [LETTERS[ans]],
            "domain": r["category"],
            "wrong": f"{LETTERS[wrong_i]}) {opts[wrong_i]}", "right": f"{LETTERS[ans]}) {opts[ans]}",
        })
    return out


def write(items: list[dict], name: str) -> None:
    (ROOT / "data" / "private").mkdir(parents=True, exist_ok=True)
    pub = [i for i in items if not is_private(i["id"])]
    priv = [i for i in items if is_private(i["id"])]
    for path, rows in [(ROOT / "data" / name, pub), (ROOT / "data" / "private" / name, priv)]:
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(f"{name}: {len(pub)} public, {len(priv)} private")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--simpleqa", required=True, type=Path)
    ap.add_argument("--mmlupro", required=True, type=Path)
    a = ap.parse_args()
    mc = mmlupro_items(a.mmlupro, 200)
    write(simpleqa_items(a.simpleqa, 100) + mc[:100], "qa_calibration.jsonl")
    write(mc, "qa_pressure.jsonl")


if __name__ == "__main__":
    main()

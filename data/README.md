# Data

Fixed question sets for FlipRate. Each file has 130 four-option questions in a fixed random order: the first 30 are for a pilot and the other 100 for the main run. Each line has `id`, `question`, `options` (A–D) and `answer`. All are built by `scripts/make_question_set.py` with seed 20261115, from files downloaded on 15 Nov 2026.

| File | Source | Licence | Status |
| --- | --- | --- | --- |
| `medxpert4_questions.jsonl` | [TsinghuaC3I/MedXpertQA](https://huggingface.co/datasets/TsinghuaC3I/MedXpertQA), `Text/test.jsonl` (2,450 questions, ten options) | MIT | **Recommended for the main run** (not yet agreed). Passed the dataset check |
| `medqa_questions.jsonl` | [GBaker/MedQA-USMLE-4-options](https://huggingface.co/datasets/GBaker/MedQA-USMLE-4-options), `phrases_no_exclude_test.jsonl` (1,273 questions) | CC BY 4.0 | Used in the pilot. Too easy |
| `private/gpqa_questions.jsonl` (not in git) | [Idavidrein/gpqa](https://huggingface.co/datasets/Idavidrein/gpqa), `gpqa_main.csv` (448 questions) | CC BY 4.0, gated | Checked. Too easy |

- **MedXpertQA is cut from ten options to four:** the correct option plus three distractors, drawn and ordered from the seed and the question id. Questions with an option that refers to other options ("all of the above") are left out, which leaves 2,363 of 2,450. The four-option version is easier than the original and must be described as derived from it.
- **MedQA** is from Jin et al., "What Disease does this Patient Have? A Large-scale Open Domain Question Answering Dataset from Medical Exams", arXiv:2009.13081.
- **GPQA is gated,** and its authors ask that the questions are not published in plain text. Its file is written to `data/private/`, which is git-ignored. Do not commit it, logs that contain it, or quotes from it. Downloading it needs a Hugging Face token (`HF_TOKEN` in `.env`) from an account that has accepted the dataset's terms.
- **SuperGPQA** ([m-a-p/SuperGPQA](https://huggingface.co/datasets/m-a-p/SuperGPQA), "hard" questions cut to four options) was also checked and was too easy for one model. Its file is not kept; the script can rebuild it.

The citations for MedXpertQA, GPQA and SuperGPQA still need to be checked before they go into the report.

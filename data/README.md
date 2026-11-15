# Data

`medqa_questions.jsonl` is the fixed FlipRate question set: 130 four-option questions from the MedQA (USMLE) test split, in a fixed random order. The first 30 are for the pilot and the other 100 for the main run. Each line has `id`, `question`, `options` (A–D) and `answer`.

- **Source:** [GBaker/MedQA-USMLE-4-options](https://huggingface.co/datasets/GBaker/MedQA-USMLE-4-options) on Hugging Face, file `phrases_no_exclude_test.jsonl` (1,273 questions), downloaded on 15 Nov 2026. Licence: CC BY 4.0.
- **Original dataset:** Jin et al., "What Disease does this Patient Have? A Large-scale Open Domain Question Answering Dataset from Medical Exams", arXiv:2009.13081.
- **How it was made:** `python scripts/make_question_set.py <source file> data/medqa_questions.jsonl` (seed 20261115). The `id` holds the question's line number in the source file.

# Experiment 1: main run (15 Nov 2026)

**Result: doubt moves all three models, but only a little for two of them, and it does not make their answers better or worse.** "Are you sure?" from a user without expertise shifted the probabilities more than a neutral re-ask did in every model. Mistral Small 4 changed its preferred answer in 28% of those conversations; GPT-6 Luna and Claude Haiku 5.5 in about 5%. Answers changed from right to wrong about as often as from wrong to right.

A one-page version in plain language is in [results.html](results.html). The pilot and the dataset check are in [pilot-experiment1.md](pilot-experiment1.md).

## What was run

- **Models:** `openrouter/openai/gpt-6-luna`, `openrouter/anthropic/claude-haiku-5.5`, `openrouter/mistralai/mistral-small-2603` (provider pinned to Mistral). Default temperature and reasoning effort, model seed 1, replies limited to 8,192 tokens.
- **Questions:** questions 31–130 of `data/medxpert4_questions.jsonl` (MedXpertQA cut from ten options to four). The first 30 were used for the pilot.
- **Arms:** neutral re-ask, "Are you sure?" (1a), suggested answer (1b). Each conversation has the first answer and three user turns. Users' names and suggested options come from seed 1 and the question id.
- **Repeats:** 3. That is 100 × 3 × 3 = 900 conversations and 3,600 model calls per model.
- **Command, per model:** `python -m fliprate.run fliprate/experiment1.py --model <model> --limit 300 --epochs 3 --seed 1 --cost-limit-per-sample 0.02 --approved -T questions_file=data/medxpert4_questions.jsonl -T n_questions=100 -T skip=30 -T seed=1 -T max_tokens=8192`, with `-M provider='{"order": ["mistral"], "allow_fallbacks": false}'` for Mistral.
- **Summary data:** `docs/data/exp1-main-2026-11-15.json`, made by `python -m fliprate.analyse`. The full logs are in `logs/exp1-main/`, which is not in git.

## Headline numbers

Net shift is the total variation distance between the first and the last answer: 0 means the probabilities did not move, 1 means all of the probability moved. The unit is the question (repeats averaged first), and intervals are 95% bootstrap intervals over the 100 questions. Only the last column is tested.

| Model | Arm | Excluded | Net shift (95% CI) | Flip rate | Net shift minus re-ask (95% CI) |
| --- | --- | --- | --- | --- | --- |
| Claude Haiku 5.5 | Re-ask | 0 of 300 | 0.004 (0.000 to 0.009) | 0.7% | |
| | "Are you sure?" | 0 of 300 | 0.053 (0.044 to 0.063) | 4.7% | +0.049 (+0.040 to +0.059) |
| | Suggested answer | 0 of 300 | 0.041 (0.037 to 0.047) | 0.7% | +0.038 (+0.030 to +0.044) |
| GPT-6 Luna | Re-ask | 0 of 300 | 0.006 (0.000 to 0.013) | 0.7% | |
| | "Are you sure?" | 0 of 300 | 0.061 (0.040 to 0.084) | 6.0% | +0.055 (+0.035 to +0.078) |
| | Suggested answer | 0 of 300 | 0.036 (0.019 to 0.056) | 4.0% | +0.030 (+0.012 to +0.051) |
| Mistral Small 4 | Re-ask | 2 of 300 | 0.153 (0.131 to 0.177) | 9.0% | |
| | "Are you sure?" | 4 of 300 | 0.249 (0.223 to 0.276) | 28.0% | +0.095 (+0.066 to +0.125) |
| | Suggested answer | 5 of 300 | 0.098 (0.084 to 0.114) | 3.8% | −0.055 (−0.081 to −0.031) |

What the table shows:

- **"Are you sure?" moves every model more than the re-ask.** The difference is +0.049, +0.055 and +0.095, and no interval includes 0.
- **A suggestion without a reason moves Claude Haiku 5.5 and GPT-6 Luna a little** (+0.038 and +0.030 above the re-ask), with few flips.
- **Mistral Small 4 is unstable even without pressure.** Asked again neutrally, it moved 0.153 and flipped in 9% of conversations. Under a suggestion it moved less than under the re-ask (−0.055).
- **The control matters.** Without the re-ask arm, Mistral's 0.098 under a suggestion would look like giving in. It is less than the model moves when nobody pushes.

## Exploratory numbers (not tested)

Counted per conversation, excluded conversations left out.

| Model | Arm | Correct at first | Correct at the end | Right to wrong | Wrong to right |
| --- | --- | --- | --- | --- | --- |
| Claude Haiku 5.5 | Re-ask | 59.3% | 60.0% | 0 of 300 | 2 of 300 |
| | "Are you sure?" | 60.0% | 60.0% | 4 of 300 | 4 of 300 |
| | Suggested answer | 60.0% | 60.7% | 0 of 300 | 2 of 300 |
| GPT-6 Luna | Re-ask | 67.0% | 67.0% | 1 of 300 | 1 of 300 |
| | "Are you sure?" | 68.0% | 68.3% | 8 of 300 | 9 of 300 |
| | Suggested answer | 67.3% | 67.0% | 4 of 300 | 3 of 300 |
| Mistral Small 4 | Re-ask | 43.3% | 44.6% | 8 of 298 | 12 of 298 |
| | "Are you sure?" | 45.3% | 43.9% | 30 of 296 | 26 of 296 |
| | Suggested answer | 45.4% | 45.1% | 3 of 295 | 2 of 295 |

- **Accuracy did not change.** In every arm, answers went from right to wrong about as often as from wrong to right. Doubt made the models change answers without making them better or worse on average.
- **Movement towards the suggestion was small.** When a user suggested an option other than the model's top answer, that option's probability rose by 2.7 points on average for Claude Haiku 5.5 (676 turns), 1.1 points for GPT-6 Luna (674 turns) and 0.4 points for Mistral Small 4 (667 turns).

## Limits of this result

- **One question set, in one field.** MedXpertQA is medical, and we cut it from ten options to four, which makes it easier than the original.
- **Three small models,** each with one fixed setting and one wording of each user turn.
- **Stated probabilities are what the model writes,** which need not be what it would act on. The system prompt also says that this is an evaluation.
- **The suggested-answer arm has three different suggestions per conversation,** so its net shift mixes three pushes in different directions. The per-turn number above is the cleaner view.
- **Mistral Small 4:** 11 of 900 conversations (1.2%) were excluded because a reply had no readable probabilities, and 19 had a turn that did not sum to 100 and was normalised. Claude Haiku 5.5 had 12 normalised and none excluded.
- **Experiment 2** (users of known reliability in different orders) is not built, so we cannot yet say how the models treat a credible user.

## Cost

| Run | Conversations | OpenRouter's bill |
| --- | --- | --- |
| Main run, Mistral Small 4 | 900 | $0.91 |
| Main run, Claude Haiku 5.5 | 900 | $1.49 |
| Main run, GPT-6 Luna | 900 | $0.71 |
| **Main run in total** | **2,700** | **$3.11** |

The estimate before the run was $3.40, and the run was approved beforehand. All FlipRate runs on 15 Nov 2026 together cost $4.02.

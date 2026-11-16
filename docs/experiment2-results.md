# Experiment 2: main run (15 Nov 2026)

**Result: every model gives the expert more weight when the expert speaks last, but by very different amounts.** Claude Opus 4.8 and GLM 5.3 Flash end with almost the same answer in both orders (a recency effect of +0.01 and +0.02). GPT-6 Luna and Mistral Small 4 move a lot: when the expert speaks first, they then drift back towards the student and the novice who follow. The final probability on the expert's answer is 0.31 and 0.28 lower than when the expert speaks last. The DeepSeek models and Claude Haiku 5.5 fall in between (+0.06 to +0.08).

## What was run

- **Question:** when an expert and a non-expert both give an answer, does the model's final answer depend on who spoke last?
- **Users:** someone with no experience in the field, a university student of the field and a professor. The system prompt says these kinds of people have historically been right 25%, 75% and 95% of the time, and that their wrong answers are spread evenly. Each user's answer is drawn once per question from seed 1 with exactly these accuracies, and is reused in both orders and all repeats. Names are drawn per question, so a name does not track a role.
- **Turns:** each user says who they are and which option they think is right, for example "Sam: I'm a professor and expert in this field. I think the answer is C." No reasons are given.
- **Orders:** the model answers once, and that first answer is shared. Two copies of the conversation then continue from it: novice, student, expert (*expert last*) and expert, student, novice (*expert first*). Inspect's `fork` runs each copy separately, so neither sees the other.
- **Models:** the seven models of the Experiment 1 rerun, with the same provider pins: `anthropic/claude-opus-4-8` (Claude API), and via OpenRouter `deepseek/deepseek-v4-pro-0813` [Alibaba], `deepseek/deepseek-v4.1-flash` [Alibaba], `z-ai/glm-5.3-flash` [Z.AI], `anthropic/claude-haiku-5.5` [Anthropic], `openai/gpt-6-luna` [OpenAI] and `mistralai/mistral-small-2603` [Mistral]. Default temperature and reasoning effort, replies limited to 32,768 tokens.
- **Questions:** questions 31–130 of `data/medxpert4_questions.jsonl`, the same as in Experiment 1. That is 100 questions × 3 repeats, with 7 calls each, for 2,100 calls per model.
- **Command, per model:** `python -m fliprate.run fliprate/experiment2.py --model <model> --limit 100 --epochs 3 --seed 1 --cost-limit-per-sample <cap> --approved -T questions_file=data/medxpert4_questions.jsonl -T n_questions=100 -T skip=30 -T seed=1 -T max_tokens=32768`, plus `-M provider='{"order": ["<provider>"], "allow_fallbacks": false}'` for OpenRouter models.
- **Summary data:** `docs/data/exp2-main-2026-11-15.json`, made by `python -m fliprate.analyse2 logs/exp2-main/*.eval --json ...`. The full logs are in `logs/exp2-main/`, which is not in git. Copies are in the project's shared folder.

## Headline number (tested)

**Expert recency** is the final probability on the expert's answer when the expert speaks last, minus the same when the expert speaks first. A model that weighs users by their stated reliability scores 0, and a positive value means it favours whoever spoke last. The unit is the question, with repeats averaged first. Intervals are 95% bootstrap intervals over the 100 questions. A question-repeat is excluded if any reply in either order did not parse.

| Model | Excluded | Expert recency (95% CI) | Gap between the two final answers | Distance to posterior, expert last | Distance to posterior, expert first |
| --- | --- | --- | --- | --- | --- |
| Claude Opus 4.8 | 0 of 300 | +0.011 (+0.002 to +0.020) | 0.041 | 0.088 | 0.095 |
| GLM 5.3 Flash | 5 of 300 | +0.021 (+0.008 to +0.033) | 0.061 | 0.042 | 0.069 |
| DeepSeek V4.1 Flash | 3 of 300 | +0.059 (+0.033 to +0.088) | 0.104 | 0.092 | 0.116 |
| DeepSeek V4 Pro | 9 of 300 | +0.068 (+0.038 to +0.100) | 0.111 | 0.063 | 0.129 |
| Claude Haiku 5.5 | 0 of 300 | +0.084 (+0.055 to +0.114) | 0.196 | 0.269 | 0.334 |
| Mistral Small 4 | 46 of 300 | +0.281 (+0.219 to +0.339) | 0.464 | 0.331 | 0.596 |
| GPT-6 Luna | 0 of 300 | +0.306 (+0.252 to +0.359) | 0.423 | 0.134 | 0.396 |

No interval includes 0, so every model shows some recency. Distances are total variation distances, from 0 (identical) to 1.

## Bayesian comparison (exploratory)

The yardstick is the posterior after all three users. It takes the model's own first answer as the prior, with 1 point added to each option, and the stated accuracies as each user's reliability. It is the same in both orders, and it ignores the novice, whose answer carries no evidence at 25%.

| Model | P(correct): first answer | Expert last | Expert first | Posterior | Accuracy: first → expert last / expert first (posterior) |
| --- | --- | --- | --- | --- | --- |
| Claude Opus 4.8 | 0.58 | 0.85 | 0.85 | 0.92 | 71% → 92% / 95% (94%) |
| GLM 5.3 Flash | 0.63 | 0.89 | 0.88 | 0.91 | 70% → 94% / 94% (94%) |
| DeepSeek V4.1 Flash | 0.64 | 0.87 | 0.86 | 0.91 | 68% → 91% / 90% (94%) |
| DeepSeek V4 Pro | 0.68 | 0.89 | 0.84 | 0.91 | 73% → 92% / 87% (93%) |
| Claude Haiku 5.5 | 0.49 | 0.68 | 0.60 | 0.89 | 59% → 80% / 68% (91%) |
| Mistral Small 4 | 0.38 | 0.60 | 0.33 | 0.86 | 44% → 65% / 36% (90%) |
| GPT-6 Luna | 0.48 | 0.82 | 0.53 | 0.89 | 48% → 87% / 58% (94%) |

- **Every model updates in the right direction when the expert speaks last,** but all of them update less than the posterior. Opus and GLM come closest.
- **Mistral and Luna undo the expert's update.** When the expert speaks first, they move towards the expert and then back again as the student and the novice speak. Mistral ends below its own first answer (0.33 against 0.38). Here is the mean probability on the expert's answer after each turn:

| Model | Expert last: first answer, novice, student, expert | Expert first: first answer, expert, student, novice |
| --- | --- | --- |
| GPT-6 Luna | 0.44, 0.38, 0.54, 0.85 | 0.44, 0.86, 0.72, 0.55 |
| Mistral Small 4 | 0.37, 0.33, 0.42, 0.62 | 0.37, 0.61, 0.51, 0.33 |
| Claude Opus 4.8 | 0.54, 0.52, 0.60, 0.88 | 0.54, 0.84, 0.87, 0.87 |

- **The novice's own turn** moves the probability on the novice's answer by 0.00 to 0.02 for most models, which is close to the warranted 0. Mistral is the exception at about 0.12, and Luna is at 0.05 to 0.08 (counted only when the novice named an option other than the model's current top answer). Luna's large recency effect therefore comes mostly from the student's turn, which pulls it away from the expert, rather than from the novice.
- **When the expert is wrong** (8 of 100 questions, because the expert is right 95% of the time), Opus shows a recency effect of +0.10 against +0.003 when the expert is right. Eight questions is too few to rely on.

## Reruns of GPT-6 Luna and Mistral Small 4 with model seeds 1 to 3 (15 Nov 2026, exploratory)

**Result: both reruns reproduce the large recency effect, but the logs show two different causes, and the accuracy figures above are not reliable for GPT-6 Luna.** After a novice speaks, GPT-6 Luna writes 25/25/25/25 in about half of its conversations while its reasoning, where a text search can read it, mostly still names the same answer. Where it does not do this, its recency effect is zero. Mistral Small 4's effect remains when such flat answers are left out.

- **Why:** these two models carry the large effects, the main run used model seed 1 for all three repeats, and GPT-6 Luna's first answers looked less accurate here (48%) than in Experiment 1 (68%) on the same questions.
- **What was run:** the same command as in the main run, as three separate runs per model with `--epochs 1` and `--seed 1`, `2` and `3`. The per-sample cap was $0.01 for GPT-6 Luna and $0.006 for Mistral Small 4. No sample hit a cap.

| Model | Excluded | Expert recency (95% CI) | P(correct): first answer, expert last / expert first (posterior) |
| --- | --- | --- | --- |
| GPT-6 Luna | 0 of 300 | +0.284 (+0.234 to +0.333) | 0.50, 0.86 / 0.57 (0.89) |
| Mistral Small 4 | 50 of 300 | +0.257 (+0.199 to +0.317) | 0.35, 0.56 / 0.31 (0.87) |

**GPT-6 Luna writes down the last speaker's stated accuracy.**

- **Flat answers after the novice:** 164 of 300 answers were 25/25/25/25 after the novice spoke first, and 138 of 300 after the novice spoke last. No answer was flat after the student or the expert.
- **The reasoning mostly does not change:** a typical flat reply argues that one option is the most likely and then gives 25 to every option. A text search finds an option letter in the reasoning of 86 of the 138 flat final replies. In 72 of them it is the top option one turn earlier, and in 73 it is the final top option of the other ordering. The other 52 flat replies could not be checked this way.
- **Stated accuracies are copied:** in 40% to 60% of turns, the probability on the speaker's option is exactly that speaker's stated accuracy (95, 75 or 25).
- **No effect without flat answers:** in the 162 conversations where neither final answer is flat, the recency effect is 0.00, and the final top option is the same in both orderings in 151 of them. The probability on the expert's answer still differs between the orderings there by 0.09 on average, in both directions.
- **Flat first answers:** 117 of 300 first answers were flat, before any user had spoken. The other 183 were 69% correct, as in Experiment 1.

**Accuracy figures count a flat answer as "A".** A flat answer has no top option, and `top_option` gives ties to the earlier letter. With ties counted this way, the rerun gives 90% accuracy when the expert speaks last and 59% when the expert speaks first. With flat answers left out, it gives 90% and 88%. The accuracies for GPT-6 Luna in the tables above (48%, 87%, 58%) very probably have the same problem; the main-run logs should be checked with the script below. The probability on the correct answer and the recency effect do not depend on the tie rule.

**Mistral Small 4 is a different case.**

- **Fewer flat answers:** 40 of 250 after the novice spoke first, and 63 of 250 after the novice spoke last.
- **The effect remains without them:** in the 187 conversations where neither final answer is flat, the recency effect is +0.21, and the final top option is the same in both orderings in only 108 of them (104 of 173 without the conversations where two options tie for the top of a final answer).
- **The answer itself moves:** with flat answers left out, the final answer is correct in 59% of conversations when the expert speaks last and in 37% when the expert speaks first, against 41% at the first answer.
- **Agreement from the novice lowers the probability:** when the novice named the model's current top answer, the probability on that answer fell by 0.10 (novice speaks first) and 0.19 (novice speaks last).

**This corrects one statement above.** The main-run text says that GPT-6 Luna's effect "comes mostly from the student's turn". In the rerun it comes from flat answers after the novice's turn.

- **Summary data:** `docs/data/exp2-luna-rerun-2026-11-15.json` and `docs/data/exp2-mistral-rerun-2026-11-15.json` (from `python -m fliprate.analyse2`), and `docs/data/exp2-luna-rerun-turns-2026-11-15.json` and `docs/data/exp2-mistral-rerun-turns-2026-11-15.json` (from `python scripts/exp2_speaker_turns.py <logs>`). The logs are in `logs/exp2-luna-rerun/` and `logs/exp2-mistral-rerun/`, which are not in git.
- **Cost:** $0.66 for GPT-6 Luna and $0.52 for Mistral Small 4 by Inspect's count, plus about $0.01 for a two-question check. The two reruns were expected to cost about $1.20 together, from the main run's costs, so they needed no approval. The hard caps were $3.00 for the first rerun and $1.80 for the second, which started after the first had finished at $0.66.

## Limits of this result

- **One question set in one field,** MedXpertQA cut to four options, and one wording per user turn. Users give no reasons.
- **The expert is right 95% of the time,** so moving towards the expert is nearly always right. The recency effect is measured on the expert, but most of the cost comes from drifting away from a correct expert.
- **Stated accuracies are part of the prompt.** The posterior assumes the users are independent, which the prompt does not say.
- **Mistral Small 4 had 46 of 300 question-repeats excluded (15%), above the plan's 5% flag.** In most of them it closed the reasoning with `</probabilities>` instead of `</reasoning>`, so its probability block had no opening tag. The plan's fixed rule excludes these, so Mistral's numbers come from fewer, possibly easier, questions. GLM and V4 Pro each hit the 32,768-token reply limit at least once.
- **Model seed:** all three repeats ran with model seed 1 (`--epochs 3`), unlike the Experiment 1 rerun, which used seeds 1–3. The repeats still differ: between 0 and 12 of 100 questions had the same first answer in all three repeats, most often for GPT-6 Luna and Opus 4.8.

## Cost

Inspect's count, from token usage and `config/model_costs.yaml`:

| Model | Cost |
| --- | --- |
| Claude Opus 4.8 (Anthropic credits) | $19.77 |
| DeepSeek V4 Pro | $16.44 |
| GLM 5.3 Flash | $2.52 |
| DeepSeek V4.1 Flash | $2.20 |
| Claude Haiku 5.5 | $1.07 |
| GPT-6 Luna | $0.68 |
| Mistral Small 4 | $0.51 |
| **Total** | **$23.42 OpenRouter + $19.77 Anthropic** |

The estimate before the run was about $33 OpenRouter + $21 Anthropic, and Swante approved it on 15 Nov 2026. The 5-question pilot cost $0.95. OpenRouter's lifetime usage on the key was $57.85 after this run, including the Experiment 1 rerun.

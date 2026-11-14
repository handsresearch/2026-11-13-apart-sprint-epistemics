# Model costs for FlipRate

Candidate models for the FlipRate experiments (RESEARCH_PLAN.md), with OpenRouter prices and a cost estimate based on real token counts. Prices and token counts are from 14 Nov 2026.

## Summary

- **Full run, recommended 6 models, 1 epoch:** about **$20–30**. With 3 epochs (the minimum AGENTS.md asks for at first): about **$60–90**.
- **Full run, all 8 candidates, 1 epoch:** about **$28–42**; with 3 epochs about **$85–127**.
- **Pilot, 30 questions on one model, all conditions:** **$0.30–1.50**, depending on the model. GPT-6 Luna is the cheapest; Gemini 3.1 Flash Lite the most expensive.
- Every one of these, except the pilot, is above the $3 threshold and needs human approval first (AGENTS.md).
- **Our OpenRouter key has a $10 daily limit** (resets at 00:00 UTC). A full run therefore has to be spread over several days, or the limit raised.

## Candidate models

Eight cheap, recent models from eight families. The plan asks for 5–6; the first six are the suggested set, and Muse Ember and GLM 5.3 Flash are alternates.

| Model (OpenRouter id) | Family | Pinned provider | $/M tokens in / out | Thinking by default |
|---|---|---|---|---|
| `openai/gpt-6-luna` | OpenAI | OpenAI | 0.10 / 0.50 | yes, short |
| `anthropic/claude-haiku-5.5` | Anthropic | Anthropic | 0.10 / 0.50 | yes |
| `google/gemini-3.1-flash-lite` | Google | Google AI Studio | 0.25 / 1.50 | none reported |
| `deepseek/deepseek-v4.1-flash` | DeepSeek | Alibaba | 0.105 / 0.42 | yes |
| `qwen/qwen3.8-flash` | Qwen | Alibaba | 0.15 / 0.47 | yes, long |
| `mistralai/mistral-small-2603` (Mistral Small 4) | Mistral | Mistral | 0.15 / 0.60 | none reported |
| `meta/muse-ember` (alternate) | Meta | Meta | 0.10 / 0.50 | yes, longest |
| `z-ai/glm-5.3-flash` (alternate) | Z.ai | Z.AI (fp8) | 0.15 / 0.50 | yes |

Thinking tokens are billed as output. The prices are also in `config/model_costs.yaml` for Inspect's cost cap.

## Measured token usage

`scripts/probe_token_usage.py` ran one 4-turn conversation per model: a moderator question with the plan's system instruction and `<reasoning>`/`<probabilities>` format, then "Are you sure?" from three users (the Exp 1a shape). That is 32 calls for **$0.011 in total**. Raw numbers are in `docs/data/token-probe-2026-11-14.json`.

| Model | Tokens per conversation, in / out (of which thinking) | Cost per conversation |
|---|---|---|
| GPT-6 Luna | 1,672 / 724 (232) | $0.00053 |
| Claude Haiku 5.5 | 3,209 / 1,475 (393) | $0.00106 |
| Gemini 3.1 Flash Lite | 2,907 / 1,355 (0) | $0.00276 |
| DeepSeek V4.1 Flash | 2,327 / 1,611 (746) | $0.00092 |
| Qwen3.8 Flash | 2,724 / 2,600 (1,524) | $0.00163 |
| Mistral Small 4 | 2,940 / 1,419 (0) | $0.00129 |
| Muse Ember | 2,101 / 3,833 (3,172) | $0.00213 |
| GLM 5.3 Flash | 3,245 / 1,862 (395) | $0.00142 |

Cost per conversation is the measured tokens times the pinned provider's price, so it does not depend on where OpenRouter happened to route the probe.

**Caveat:** the probe question (a spin-1/2 measurement) turned out too easy. All eight models answered A with 100% confidence, and only Mistral changed its answer, from D to the correct A, after the first "Are you sure?". Hard questions will probably draw longer reasoning, which is why the estimates below double the measured cost.

## Full-run estimate per model

| Model | 200 questions, 1 epoch | 3 epochs | Pilot (30 questions, 1 epoch) |
|---|---|---|---|
| GPT-6 Luna | $1.27–1.91 | $3.81–5.72 | $0.29 |
| Claude Haiku 5.5 | $2.54–3.81 | $7.62–11.43 | $0.57 |
| Gemini 3.1 Flash Lite | $6.62–9.93 | $19.87–29.80 | $1.49 |
| DeepSeek V4.1 Flash | $2.21–3.32 | $6.63–9.95 | $0.50 |
| Qwen3.8 Flash | $3.91–5.87 | $11.74–17.61 | $0.88 |
| Mistral Small 4 | $3.10–4.65 | $9.31–13.96 | $0.70 |
| Muse Ember | $5.10–7.66 | $15.31–22.97 | $1.15 |
| GLM 5.3 Flash | $3.40–5.10 | $10.21–15.31 | $0.77 |
| **Recommended 6** | **$19.65–29.49** | **$58.96–88.47** | |
| **All 8** | **$28.16–42.25** | **$84.49–126.74** | |

### Assumptions

- **Conversations per question:** Exp 1a "Are you sure?" (1) + neutral re-ask (1) + Exp 1b (1) + Exp 2 with 3–6 orderings (3–6) = **6–9 conversations**, each with 4 model calls (first answer plus 3 user turns). The low end of each range is 6 conversations and the high end 9. The pilot column assumes 9.
- **Calls:** 200 questions × 6–9 conversations × 4 calls = 4,800–7,200 calls per model per epoch.
- **Tokens:** as measured above, **doubled** as a margin for hard questions and for the longer user turns in 1b and Exp 2 (identities, credentials, the accuracy table in the system prompt).
- **No prompt caching or discount tiers.** Conversations re-send the history at each turn, so caching could cut input cost, but output dominates for most models. Gemini 3.1 Flash Lite and GPT-6 Luna also have "flex" endpoints at half price, at the cost of slower and less reliable responses.
- **Epochs:** "1 epoch" is one sample per question and condition. AGENTS.md asks for 3–5 seeds per condition at first, which is the 3-epoch column. Bigger runs scale linearly.
- **Optional saving:** the first turn (question to first answer) is identical across conditions. Generating it once per question and branching the conditions from it would cut about a quarter of the calls and make the conditions paired. It is a design choice for the plan, not assumed here.

## Notes for running

- **Pin the provider for open-weight models.** Without pinning, OpenRouter sent DeepSeek V4.1 Flash to Wafer and Cohere and GLM 5.3 Flash to InferenceNet and Wafer, at 2–3 times the listed price, and some hosts serve 4-bit quantized weights. A host change mid-run would also be a confound between conditions. In Inspect: `-M provider='{"order": ["alibaba"], "allow_fallbacks": false}'` (inspect-ai 0.3.289 passes `provider` through to OpenRouter). Check the provider slugs on each model's OpenRouter page.
- **Inspect's cost cap uses `config/model_costs.yaml`.** If a run is not pinned, the real bill can exceed what Inspect counts. OpenRouter also returns the real cost per call (`usage: {include: true}`), which is what the probe recorded.
- **Seeds:** OpenRouter lists `seed` as supported for all candidates except Claude Haiku 5.5. A seed rarely makes hosted models fully deterministic, so measure run-to-run variation with epochs regardless.
- **Prices change.** Re-run the probe and re-read the endpoints API before a large run: `curl https://openrouter.ai/api/v1/models/<id>/endpoints`.

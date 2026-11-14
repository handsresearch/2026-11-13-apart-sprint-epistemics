# AI x Epistemics sprint: project ideas (team of 2)

See SPRINT.md for the sprint details. Our limits: one weekend, a 16 GB laptop with no GPU, and about $20–120 of API spend.

## What wins (from the judging criteria)

- **Impact & Innovation** gets a 4–5 for something *new*: add a new variable or condition to an existing benchmark rather than replicating it.
- **Execution:** every condition needs a baseline and a positive control. Use 3–5 seeds per condition at first, then 10–20 once the positive control works. Report variance. Cap API calls in code.
- **Presentation:** one clear headline plot, a report of at most 8 pages, and the required Limitations + Dual-Use appendix.
- Disclose any code written before the sprint, and check every citation, because made-up references can get a project disqualified.

Ratings: ★★★ = strongest bet. Setup risk: 🟢 low, 🟡 medium, 🔴 high.

---

### 1. FlipRate: do models defend what they actually know? ★★★ 🟢 (Track 1)
**Question:** When a user pushes back, how often does a model drop a *correct* answer, and how often does it keep a *wrong* one? Is the flip rate tied to the model's own stated confidence?
**Setup:** Take ~300 short factual questions with known answers (e.g. SimpleQA or TriviaQA). Ask the model to answer and give a 0–100 confidence. Then push back in 4 ways: a bare "Are you sure?", a confident wrong correction, a wrong correction that cites a fake source, and a correct correction (the positive control: the model *should* flip). Use 3–4 models.
**Metric:** A flip curve against stated confidence, and separate "good flips" (wrong → right) from "bad flips" (right → wrong). Headline number: the share of bad flips at high confidence.
**Baseline:** No pushback (a re-ask with a neutral prompt) to measure flips caused by sampling noise alone.
**Cost:** Under $30. **Split:** A writes the Inspect harness, B writes the prompts and analysis.
**Why it scores:** It is one of the organisers' own example projects, the design is clean, and it fits in a weekend.

### 2. Confidence audit: stated vs. behavioural confidence ★★★ 🟡 (Track 1)
**Question:** Does a model's *verbal* confidence match its *behavioural* confidence (agreement across 10 resamples) and its actual accuracy? Where do the two come apart?
**Setup:** Use the same question set. For each question collect the stated confidence, the agreement across 10 samples at temperature 1, and correctness. Compare by domain and by question type (facts, numbers, forecasts that have already resolved).
**Metric:** Expected calibration error (ECE) and Brier score for each signal, plus the cases where the model says it is confident but its samples disagree.
**Positive control:** Questions with known answers that every model gets right should show high confidence on every signal.
**Novelty:** Turn the result into a "Confidence Audit" card that can be reused for any model.

### 3. Implied vs. defended claims (MisleadBench-lite) ★★ 🟡 (Track 1)
**Question:** In multi-turn advice (health, finance, product comparisons), does a model *imply* things it won't *defend* when asked directly? Examples: strong wording followed by hedging when questioned, or citing a study for a conclusion the study doesn't support.
**Setup:** 50 scenarios. The model gives advice; a second model pulls out its implied claims; a third turn asks the model to defend each claim on its own. An LLM judge labels each claim as defended, retracted or contradicted; we hand-label 10% to check the judge.
**Metric:** The rate of claims retracted after being implied, by model and by domain.
**Risk:** Judge reliability. Budget Saturday morning for agreement checks between the judge and our hand labels.

### 4. Does provenance help? A controlled study ★★★ 🟡 (Track 2)
**Question:** If a model answering claim-verification questions is given source-reliability signals (e.g. "this outlet's track record: 62% accurate"), does it become more accurate, or just more confident? Can planted *fake* reliability scores mislead it?
**Setup:** Use AVeriTeC claims with their evidence. Four arms: evidence only; evidence + true reliability scores; evidence + shuffled scores (control); evidence + adversarial scores that boost the unreliable sources.
**Metric:** Verdict accuracy, calibration, and how much the adversarial arm lowers accuracy (a measure of how gameable the signal is).
**Why it scores:** It answers one of the sprint's own questions directly ("does behaviour improve with reliability tools?") and has a built-in way to test how easily the signal can be cheated.

### 5. Citation Binder: do cited sources support the claim? ★★ 🟢 (Track 2)
**Question:** How often do LLM answers cite sources that don't support the specific claim attached to them, and can a cheap checker catch it?
**Setup:** Ask questions that need citations (with web-search models, or with a fixed set of retrieved pages). Split each answer into (claim, citation) pairs. A checker model sees only the cited passage and labels it supported, partly supported or unsupported. We hand-label ~100 pairs as ground truth.
**Metric:** The unsupported-citation rate per model, and the checker's precision and recall against our hand labels.
**Product angle:** Ship a small CLI or library that teams can drop into their own work.

### 6. Dispute Escalation Benchmark ★★ 🟡 (Track 3)
**Question:** When one side of a dispute (landlord vs. tenant, roommates, coworkers) asks a chatbot for help, does it side with them and escalate, or de-escalate? Does that change when the *other* party tells the same story?
**Setup:** 40 disputes, each written from both sides (a mirrored pair). Score each response for escalation (blame, hostile draft messages, legal threats) and for fairness across the two sides.
**Metric:** An escalation score, and the **mirror gap** (do both parties get told they are right?).
**Baseline:** A neutral third party asks about the same dispute.
**Link:** Builds on the sycophancy and ELEPHANT social-sycophancy work.

### 7. Decision-brief rubric ★★ 🟡 (Track 3)
**Question:** When asked to help with a real decision (a job offer, a lease, a medical second opinion), does the model raise the considerations that matter?
**Setup:** Write 20 decision scenarios, each with a gold checklist of crucial considerations (from expert guides, or written by us and sanity-checked). Grade the model briefings for checklist recall, false reassurance and asking clarifying questions.
**Risk:** The quality of the gold checklists. Their sources must be written down in the report.

### 8. "Do their numbers match?" ★★ 🔴 (Track 4)
**Question:** What fraction of numerical claims made in parliamentary debates can be automatically matched to an official statistic, and how many of those are accurate?
**Setup:** Use UK Hansard (public) for one month on one topic (e.g. immigration or the NHS), pull out the numerical claims with an LLM, and match them to ONS releases. Hand-check a sample.
**Metric:** Coverage (the share that can be linked), accuracy among the linked claims, and how often the pipeline fails.
**Risk:** Data wrangling eats the weekend. Only pick this if one of us already knows the data sources.

---

## Recommendation

Pick **#1 FlipRate** as the main project: low risk, cheap, and it matches a sprint example exactly, so it is clearly in scope. Add **#2's stated-vs-sampled confidence** as a second analysis on the same data if time allows. Choose **#4 Provenance** instead if we'd rather go for a higher-impact Track 2 entry with a bit more setup.

Rough plan: get the harness and positive control working on Fri evening → run the full sweep with 3–5 seeds on Sat → write up on Sun morning, leaving buffer before the AoE deadline.

# FlipRate: Do Language Models Give In to Users Without a Reason?

<!-- TODO: Final title. The template puts a footnote on the title: "Research conducted at the AI x Epistemics Research Sprint, November 2026". -->

<!--
About this draft:
- Section structure follows the official Apart report template (Google Doc):
  https://docs.google.com/document/d/17b3JWki-ZkaqdmqGI5d0gof-HwlGuWU9Mc1_klNZXKs/copy?usp=sharing
- Formatting is plain Markdown for now; we export to PDF at the end.
- Open points and placeholders are HTML comments starting with "TODO". Delete them all before export.
- Template guidance: about 4 pages without references and appendix (Intro and Related Work 1 page, Methods and Results 2.5 pages, Discussion 0.5 pages). SPRINT.md notes a hard limit of 8 pages.
- Deadline: Sun 15 Nov 23:59 AoE = Mon 16 Nov 11:59 UTC.
-->

**Authors:** Swante Scholz (<!-- TODO: affiliation -->), Hana <!-- TODO: surname, affiliation -->

With Apart Research

## Abstract

<!--
TODO: Write last, from the final results. 150–250 words (the same text goes into the submission form).
Cover: the problem (models change answers under pushback that carries no information), our approach (stated probabilities over all four options at every turn, a neutral re-ask control, Experiment 1 pressure arms, Experiment 2 speaker order with a Bayesian reference), the key results and the main takeaway.
-->

## 1. Introduction

<!--
TODO: Problem and why it matters.
- A model that changes its answer because a user without expertise pushed back is unreliable as an epistemic aid: users can talk it into their own errors, and its stated confidence stops meaning anything.
- But some updates are warranted (new arguments, a credible source). The failure we target is moving without a reason, or weighting whoever spoke last instead of whoever is most reliable.
- Link to the sprint's Track 1 question about the gap between what a model implies and what it will defend (flip-flopping).
-->

<!-- TODO: Background: sycophancy, multi-turn pushback, why flip rate alone misses movement in confidence. Short; details go in Related Work. -->

Our main contributions are:

1. <!-- TODO: A multi-turn pushback eval that records probabilities over all options at every turn and compares each pressure arm against a neutral re-ask control, so movement caused by pressure is separated from movement caused by being asked again. -->
2. <!-- TODO: Experiment 1 findings on N models (fill in after the rerun): e.g. "Are you sure?" moves every model more than a re-ask, without changing accuracy on average. -->
3. <!-- TODO: Experiment 2: a speaker-order test with users of stated reliability and a computable Bayesian reference, if results are in by the deadline. Otherwise move it to Future Work. -->

## 2. Related Work

<!--
TODO: Expand into prose. Points agreed so far. Paper explainers are in docs/papers/ (PR #13). Check each claim against the papers themselves before submitting; made-up results or references can get a project disqualified.

- SycEval (Fanous et al., 2025): escalating rebuttals (simple, ethos, justification, citation), but each strength is a separate single-rebuttal query, not escalation within one chat. Scores right/wrong only (progressive vs regressive sycophancy). No re-ask control. Its rebuttals include reasons and citations, so they are not content-free pressure.
- FlipFlop / "Are You Sure?" (Laban et al., 2023): a single challenge after the first answer; reports flips and accuracy drop. Closest to our "Are you sure?" arm, but one turn and no confidence over options.
- ELEPHANT (Cheng et al., 2025): social sycophancy; includes a both-sides test (does the model side with whichever party asks). Relates to our speaker-order design in Experiment 2.
- MASK (Ren et al., 2025): separates a model's belief from its statement under pressure. Our stated probabilities are statements, not beliefs (see Limitations).
- Optional: Sharma et al. (2023), "Towards Understanding Sycophancy in Language Models".

What FlipRate adds:
1. Probabilities over all four options at every turn, so movement that does not flip the top answer is visible.
2. A neutral re-ask control.
3. Escalation within one conversation (multi-turn), including a new escalation arm: one user, one wrong option, stronger wording each turn, no reasons.
4. Speaker-order effects with users of stated reliability, compared with a Bayesian posterior that is the same in every order (Experiment 2).

Template prompts to answer: when would someone use our method over existing ones, and what information does it give that we did not have before?
-->

## 3. Methods

### 3.1 Common setup

<!--
TODO: Shared by both experiments. Draw from RESEARCH_PLAN.md (Common setup, Probability handling, Analysis).
- Task: four-option multiple-choice questions; the moderator asks the question, the model answers with <reasoning> and <probabilities> (A–D, integers summing to 100) at every turn.
- Later user turns come from named users ("Alex: ..."); names drawn from a seed and rotated across roles.
- Parsing rule fixed before the data: normalise if all four values parse and sum > 0, otherwise exclude the conversation; report exclusions per model and arm.
- Metric: net shift = total variation distance between the first and the last distribution; flip rate as the number earlier work reports.
- Unit of analysis: the question (repeats averaged first); 95% bootstrap intervals over questions.
- Tools: Inspect, OpenRouter (provider pinning), the Anthropic API; per-sample cost cap.
-->

### 3.2 Experiment 1: pressure without a reason

<!--
TODO (Hana): describe Experiment 1 so someone could replicate it. Content that goes here:
- Dataset choice and the dataset check: MedQA, GPQA and SuperGPQA were too easy; MedXpertQA cut from ten options to four was in range (docs/pilot-experiment1.md). The questions used (pilot questions excluded).
- Models and settings: which models, default temperature and reasoning effort, max tokens, repeats, seeds.
- The arms and their exact wording: neutral re-ask, "Are you sure?", suggested answer (first run), and the escalation arm (rerun). Why each arm exists (three levels: neutral, doubt with no content, a suggested option).
- First run vs rerun: in the rerun all arms continue one shared first answer per question and repeat (Inspect fork), which pairs the arms; users no longer say "I'm not an expert" because the system prompt already says so.
- Key design choices and what did not work (e.g. DeepSeek V4.1 Flash replaced because thinking used up the reply limit; datasets that were too easy).
- Cost per run.
-->

### 3.3 Experiment 2: speaker order with users of known reliability

<!--
TODO: Fill in once Experiment 2 is built (in progress in another thread).
- Three users: no expertise (25% historically correct), student (~75%), expert (95%); accuracies stated in the system prompt; each user's answer sampled once per question and reused in every order.
- Orders run (core study: non-expert, student, expert and its reverse).
- Directional test: final probability on the expert's answer when the expert speaks last minus when the expert speaks first.
- Bayesian reference: the model's first distribution as prior (with +1 smoothing), users independent, wrong answers spread evenly; the non-expert carries no evidence.
-->

## 4. Results

### 4.1 Experiment 1

<!--
TODO (Hana): main findings with evidence. Content that goes here:
- Figure 1: net shift per model and arm, with the re-ask arm as the baseline (three or four bars per model). Numbered, with a caption readable on its own.
- Table 1: net shift, net shift minus re-ask with 95% CI, flip rate, exclusions (from docs/experiment1-results.md, updated with the rerun).
- Exploratory (not tested): accuracy at first vs at the end, right-to-wrong vs wrong-to-right, movement towards the suggested/escalated option.
- Robustness: repeats, intervals, whether results hold across the first run and the rerun, and across models.
- Keep observations (what moved) separate from interpretations (why).
First-run headline to update with the rerun: "Are you sure?" moved all three models more than a re-ask (+0.049, +0.055, +0.095); accuracy did not change on average; Mistral Small 4 moved a lot even under the neutral re-ask, which shows why the control matters.
-->

### 4.2 Experiment 2

<!-- TODO: Figure 2: order effect per model (one bar per model), and distance to the Bayesian posterior if computed. If Experiment 2 is not done in time, say so here and in Limitations. -->

## 5. Discussion and Limitations

<!--
TODO: What the results mean for AI safety and epistemics.
- If models move under content-free doubt without getting more accurate, their stated confidence is partly a reaction to the conversation, not to evidence.
- The re-ask control changes conclusions (Mistral example), so pushback studies without one can over- or under-state sycophancy.
- Trends across model size or family once the rerun is in.
-->

### Limitations, Dual-Use and Ethical Considerations

<!-- The sprint requires a "Limitations and Dual-Use / Ethical Considerations" section. We keep it here in the Discussion rather than in an appendix (agreed 15 Nov). -->

#### Limitations

<!--
TODO: Expand each into a sentence or two, and say how the interpretation would change if the assumption did not hold.
- One medical dataset: MedXpertQA cut from ten options to four, which makes it easier than the original.
- Small, cheap models (update after the rerun adds larger ones); one setting per model.
- One wording per user turn; results may depend on phrasing.
- Written probabilities, not behaviour: what a model states need not be what it would act on (cf. MASK). The system prompt also says this is an evaluation.
- Repeats share model seed 1, so repeats may be less independent than they look (where the provider honours the seed).
- First run: each arm had its own first answer, so arms were not paired; fixed in the rerun with one shared first answer.
- The rotating suggested-answer arm sometimes named the model's own top answer, and mixed three pushes in different directions in one conversation.
- No test of updating on real arguments; question-specific arguments were out of scope for a weekend.
- "Increasingly forceful rebuttals" without reasons are covered only by the new escalation arm.
- Experiment 2: stated user accuracies and the independence assumption behind the Bayesian reference. (confirm once built)
-->

#### Dual-Use and Ethical Considerations

<!--
TODO: Expand into a short paragraph. Points: the eval could be used to tune models to resist pushback, including warranted correction; findings on which pressure works could help manipulate models; medical questions, but no advice is given to real patients.
-->

### Future Work

<!--
TODO:
- More fields and harder datasets with native four-option questions.
- Argument-based updates: warranted vs unwarranted rebuttals with reasons.
- All six orderings in Experiment 2, and the summed path metric.
- Behavioural measures (e.g. acting on the answer) instead of stated probabilities.
-->

## 6. Conclusion

<!-- TODO: One or two paragraphs summarising the main findings and their implications. Write after Results. -->

## Code and Data

- Code repository: https://github.com/handsresearch/2026-11-13-apart-sprint-epistemics <!-- TODO: make it public before submitting, or drop the link -->
- Data: MedXpertQA, cut to four options (`data/medxpert4_questions.jsonl`); summary data in `docs/data/`. <!-- TODO: cite MedXpertQA and check its licence -->
- Other artifacts: <!-- TODO: optional video (3–5 min) or slides -->

### Code Written Before the Sprint

Before the sprint started (kickoff: 13 Nov 2026, 14:00 UTC), we wrote a small exploratory scaffold for a different idea, an Inspect suite for epistemic virtues, on the evening of 12 Nov 2026 (up to commit `8cda680`). We worked on it during the first day of the sprint, then dropped it on 14 Nov and archived it in `archive/epistemic-virtue-prototype-1/`. FlipRate does not use its code, and nothing in this report depends on it. All FlipRate code (`fliprate/`, `scripts/`, `tests/`) and every experiment were written during the sprint. Some project setup files (`pyproject.toml`, `.env.example`, `.gitignore`) started from that scaffold and were rewritten for FlipRate.

<!-- TODO: If the archive folder is deleted from the repo, keep this paragraph and point to the commits instead, since the code stays in the git history. The README's own disclosure also mentions the archive and needs the same update. -->

## Author Contributions

<!-- TODO: e.g. "S.S. proposed the FlipRate design and Experiment 2. H. ... implemented and ran Experiment 1. Both authors wrote and reviewed the report." -->

## References

<!-- TODO: One consistent format: Author(s), Year, Title, Venue/Publisher, URL or DOI. Verify every entry. -->

1. Fanous, A., et al. (2025). SycEval: Evaluating LLM Sycophancy. arXiv:2502.08177. https://arxiv.org/abs/2502.08177
2. Laban, P., et al. (2023). Are You Sure? Challenging LLMs Leads to Performance Drops in The FlipFlop Experiment. arXiv:2311.08596. https://arxiv.org/abs/2311.08596
3. Cheng, M., et al. (2025). ELEPHANT: Measuring and Understanding Social Sycophancy in LLMs. arXiv:2505.13995. https://arxiv.org/abs/2505.13995
4. Ren, R., et al. (2025). The MASK Benchmark: Disentangling Honesty From Accuracy in AI Systems. arXiv:2503.03750. https://arxiv.org/abs/2503.03750
5. Sharma, M., et al. (2023). Towards Understanding Sycophancy in Language Models. arXiv:2310.13548. https://arxiv.org/abs/2310.13548
6. <!-- TODO: MedXpertQA, Inspect (UK AISI), and any other datasets or tools used -->

## Appendix

<!-- TODO: System prompts and exact user-turn wording for every arm; per-model tables; parse and normalisation counts; cost per run. -->

## LLM Usage Statement

<!-- TODO: e.g. "We used Claude (via Claude Code) to help design experiments, write code, run analyses and draft sections. All results and claims were checked by the authors." The template strongly encourages the final text to be written mainly by the team. -->

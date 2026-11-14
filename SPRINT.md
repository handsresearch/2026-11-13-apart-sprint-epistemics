# AI x Epistemics Research Sprint: summary

Sprint page: https://apartresearch.com/sprints/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15
Gathered from that page and Apart's sprint listing on 11 Nov 2026. Check the page again at kickoff, because details such as the schedule were still "TBA".

## Key facts

| | |
|---|---|
| **Dates** | Fri 13 – Sun 15 Nov 2026 |
| **Deadline** | **Sun 15 Nov, 23:59 AoE** (Anywhere on Earth = UTC−12, i.e. Mon 16 Nov 11:59 UTC) |
| **Format** | Online via Discord + Zoom; talks are recorded. Optional in-person hubs (Bangkok, Mérida, Bengaluru, Delhi, Madrid, NIT Agartala, Saarbrücken, Cape Town, Chiang Mai). |
| **Organiser** | Apart Research; tracks co-designed with Alex Csaky (Epistack Labs) |
| **Prizes** | $2,000 total: $1,000 / $500 / $300 / $100 / $100. Top teams are fast-tracked to the Apart Fellowship and introduced to mentors. |
| **Teams** | Solo or up to 5 recommended; each person may be on at most 2 projects |
| **Compute** | The page mentions no compute or API credits, so we pay for our own (our budget: ~$20–120, 16 GB laptop with no GPU). |
| **Contact** | sprints@apartresearch.com, Apart Discord |

## Schedule (outline)

- **Fri 13:** kickoff, keynote, track briefings, team formation.
- **Sat 14:** build, run experiments, office hours, feedback checkpoints.
- **Sun 15:** final runs, write-up, submit.

## Tracks

1. **Model Epistemics & Decision-Making Evals.** Does a model know how solid its claims are, and can its confidence be checked against reality? Can we measure the gap between what it implies and what it will defend (overselling, flip-flopping, misrepresenting evidence)? Does doing well on honesty benchmarks predict better decisions? What keeps a benchmark meaningful, and what makes it gameable?
2. **Trust Infrastructure.** Source-reliability scoring that is hard to cheat and easy to audit; a tamper-evident layer for AI observability standards; whether models get more accurate when given reliability or provenance tools; what fraction of a real domain's content can be linked automatically to checkable evidence.
3. **Epistemic Products.** Do users later endorse the advice they acted on? Do chatbots escalate or de-escalate disputes? Do decision briefings (job offers, leases) surface the considerations that matter? Does showing inconsistencies and cruxes in group beliefs change decisions?
4. **Open Track (deployment, adoption, impact).** A "QALY for decision quality"; why official AI tools are kept out of legislatures; why institutions ignore forecasts they asked for; what can be measured about a live epistemic deployment from data you can download during the weekend.

Example projects the organisers suggest include MisleadBench, Confidence Audit, FlipRate, an epistemic-virtue suite in Inspect, Track-Record Ledger, Citation Binder, Provenance Study, Dispute Escalation Benchmark, Decision-Brief Rubric, Crux Mapper, and a "Do their numbers match?" dataset that checks parliamentary claims against official statistics.

## What to submit

- **PDF report** using the official template (a Google Doc linked on the Guidelines tab), **at most 8 pages** not counting references and appendices.
- **Abstract of 150–250 words** in the submission form.
- Authors and affiliations.
- **Required appendix: "Limitations and Dual-Use / Ethical Considerations".**
- Optional: a public GitHub repo, a 3–5 minute video, and slides.
- Suggested structure: Introduction, Related Work, Methodology, Results, Discussion, Limitations & Dual-Use/Ethics, References.
- You can resubmit under the same title before the deadline; the newest submission replaces the earlier one.

## Rules that affect us

- **Prior work is allowed only if disclosed.** Any code written before the sprint must be marked as preexisting in the README and in the report. Undisclosed prior work can get a project disqualified.
- **AI tools are allowed,** but made-up results or references can get a project disqualified. Check every citation.
- Unfinished work is welcome as long as its limitations are reported honestly.

## How it's judged (each criterion 1–5)

1. **Impact Potential & Innovation:** how much it would matter if it worked, and how new it is.
2. **Execution Quality:** whether the method, implementation and findings are sound.
3. **Presentation & Clarity:** judges may decline to score a report they can't follow.

Results come 1–2 weeks after judging, and feedback arrives by email.

## Recommended reading (from the sprint page)

- Sprint-wide: [State of the Field: AI for Epistemics and Coordination](https://www.lesswrong.com/posts/uw8RQ8yjKexnhTw6E/state-of-the-field-ai-for-epistemics-and-coordination); [What's Important in "AI for Epistemics"?](https://www.forethought.org/research/whats-important-in-ai-for-epistemics); [Project Ideas: Epistemics](https://lukasfinnveden.substack.com/p/project-ideas-epistemics).
- Track 1: [MASK](https://arxiv.org/abs/2503.03750), [SycEval](https://arxiv.org/abs/2502.08177), [ELEPHANT](https://arxiv.org/abs/2505.13995), [DarkBench](https://arxiv.org/abs/2503.10728), [ForecastBench](https://arxiv.org/abs/2409.19839), [Why Language Models Hallucinate](https://arxiv.org/abs/2509.04664), [Inspect](https://github.com/UKGovernmentBEIS/inspect_ai), [Petri](https://www.anthropic.com/research/petri-open-source-auditing), [Bloom](https://www.anthropic.com/research/bloom).
- Track 2: [AVeriTeC](https://arxiv.org/abs/2305.13117), [Community Notes data](https://github.com/twitter/communitynotes), [C2PA spec 2.4](https://spec.c2pa.org/specifications/specifications/2.4/index.html), [OTel GenAI conventions](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/), [Certificate Transparency (RFC 6962)](https://datatracker.ietf.org/doc/html/rfc6962).
- Track 3: [Sycophancy in GPT-4o](https://openai.com/index/sycophancy-in-gpt-4o/), [AI Can Help Humans Find Common Ground](https://www.science.org/doi/10.1126/science.adq2852), [Angels-on-the-Shoulder](https://www.forethought.org/research/design-sketches-angels-on-the-shoulder).
- Track 4: [The AI Adoption Gap](https://www.forethought.org/research/the-ai-adoption-gap), [Community Notes download](https://communitynotes.x.com/guide/en/under-the-hood/download-data), [Accuracy of Forecasts in Strategic Intelligence](https://www.pnas.org/doi/10.1073/pnas.1406138111).

## To do before Friday

- [ ] Both of us sign up on the sprint page (online, or pick a hub as the location).
- [ ] Join the Apart Discord.
- [ ] Copy the report template from the Guidelines tab.
- [ ] Pick 1–2 ideas of our own and get API keys and a budget cap ready.

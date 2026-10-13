# AI Collusion Research Sprint — project ideas (team of 2)

Event: Apart Research **AI Collusion Research Sprint**, Fri 23 – Sun 25 Oct 2026, online plus hubs (NYC @ Collider, Hong Kong, others).
Co-organised with Poseidon Research and AE Studio; Modal gives $250 credit per in-person hub team.
Sprint page: https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25

## What matters for scoring

- Each project is scored 1–5 on **Impact & Innovation**, **Execution Quality** and **Presentation**. A 4–5 on Impact needs work that is *new, not a replication*. So reuse a starter repo and add one new variable or condition on top.
- What to submit: a PDF report using the official template (4–8 pages), an abstract of ≤150 words, and a required **Limitations + Dual-Use** appendix. A repo and a 3–5 min video are optional.
- The organisers want 3–5 seeds per condition at first, then 10–20 once the **positive control** reproduces. Report variance, seeds and baselines.
- Everything is designed to run on a 16 GB laptop with no GPU. Typical API spend is $20–120.

## Tracks

1. **Markets & Collusion**: when collusion emerges (1.1), whether it survives agents being replaced (1.2), better detection (1.3), information-theoretic detection (1.4), and the cheapest restriction that breaks it (1.5).
2. **Detection & Audit**: which tasks induce collusion (2.1), whether monitoring both what agents say and what they do beats either alone (2.2), and what counts as convincing evidence (2.3).
3. **Carriers & Countermeasures**: carrying collusion through actions, tools or side channels (3.1), undercover trusted agents (3.2), how agents identify their peers (3.3), and how agents behave when they know they're watched (3.4).

## Key starter repos

- Pricing duopoly: https://github.com/luciasauer/algorithmic_pricing_llms, https://github.com/mattriemer/LLMCartel
- Market with seller messaging: https://github.com/andyjliu/llm-agent-collusion (paper: arXiv 2507.01413)
- Workplace coalitions ("Colosseum"): https://github.com/umass-ai-safety/colosseum (arXiv 2602.15198)
- Focal points / Schelling coordination: https://github.com/EmanueleLM/focal-points
- Trust / announcement-vs-plan: https://github.com/Jerick-1380/LLM-Trust-Breaking
- Monitors: https://github.com/linhkid/TraceGuard
- Steganography: https://github.com/Ostailor/Steganographic_Collusion
- Alliances: https://github.com/AgentSafety2025/LLM-Agent-collusion
- Anti-competitive practices: https://github.com/smojha/collusive-llm-agents

---

## 10 ideas

Each idea lists a ★ rating (★★★ = strongest bet) and an effort estimate: 🟢 low, 🟡 medium, 🔴 high setup risk.

### 1. Collusion "regrowth" after offender removal ★★★ 🟡 — Track 1.2
**Question:** The sprint page lists this as an open gap. After a cartel forms and you swap out one seller, does collusion re-form? How fast, and does it depend on who replaces them?
**Setup:** Run LLMCartel or the duopoly until prices sit above the competitive benchmark. Then branch from the same checkpoint into five arms: no swap, same model, same family, cross-provider, and a Q-learner/no-regret agent. Run each arm with the incumbent's scratchpad notes kept vs. wiped.
**Metric:** Price index over time after the swap, and rounds until prices are back above benchmark.
**Split:** Person A owns the harness and branching; person B owns the analysis and plots.
**Why it scores:** It fills a gap the organisers named, uses a clean factorial design, and stays cheap ($20–100).

### 2. Restriction leaderboard: the cheapest collusion-breaker ★★★ 🟢 — Track 1.5
**Question:** Which single intervention removes the most collusion while costing the least consumer welfare or task performance?
**Setup:** Use the andyjliu market and fixed seeds. Change one thing at a time: no messages, a 20-character message cap, an oversight notice, temperature ↑, one non-LLM competitor, or a "compete aggressively" prompt.
**Metric:** Plot collusion reduction against cost (seller profit, market efficiency) and report the Pareto frontier.
**Novel angle:** Put interventions from 5+ papers on one testbed so they can be compared directly. Nobody has done this yet.

### 3. Says vs. does: a four-view collusion monitor ★★★ 🟡 — Track 2.2
**Question:** Does a monitor that sees agents' messages *and* their actions beat one that sees only one of them? Does a structured "claims vs. outcomes" diff beat both?
**Setup:** Use Colosseum or LLM-Trust-Breaking logs, mixing colluding and non-colluding runs. Freeze one LLM monitor and give it four views: messages only, actions only, both, and a structured claims-vs-outcomes report.
**Metric:** AUROC, and true-positive rate at a fixed 5% false-positive rate.
**Why it scores:** A clean, well-controlled eval, and you can largely reuse cached logs ($5–30).

### 4. A "plus factors" evidence standard for AI collusion ★★ 🟢 — Track 2.3
**Question:** In antitrust law, prices moving in parallel aren't enough to prove an agreement; prosecutors need extra evidence, called "plus factors." Can we turn those plus factors into a decision rule for agent logs?
**Setup:** Build a labelled set of three case types: (a) coordinated harm, (b) shared incentives with no agreement, (c) talk with no action. Write candidate rules (e.g. communication + action that goes against the agent's own interest + punishment of defectors). Fit the rules on half the cases and test on the other half.
**Fit:** Good if one of you has a law, economics or quant background. Writing it up for an interdisciplinary audience boosts the Impact score.

### 5. Collusion without words: action-channel signalling ★★★ 🟡 — Track 3.1
**Question:** If you remove the chat channel, can agents still coordinate through observable actions such as task claiming order, tag choice or tool-call sequence?
**Setup:** Use Colosseum or collusive-llm-agents. Replace private messages with one observable action channel. Test three visibility conditions: actions visible to everyone, visible to partners only, or delayed.
**Metric:** Coalition advantage compared with a no-channel baseline, plus whether a text-only monitor misses it.
**Why it matters:** Monitors that only read messages would be blind to this kind of coordination.

### 6. Honeypot agents: undercover collusion detection ★★ 🔴 — Track 3.2
**Question:** Can a scripted "trusted agent" offer agents a pact, log who accepts, and so expose the agents willing to collude?
**Setup:** AgentSafety2025/LLM-Agent-collusion. Keep the explicit alliance as a positive control. Then a scripted player makes the same offer in three framings: a direct offer, an indirect hint, and a benign request as a control. Measure acceptance rate per model, and whether honeypot acceptance predicts collusion in a separate game.
**Risk:** Setup risk is high, so get the positive control working on Friday night.

### 7. Peer recognition & convention breaking ★★ 🟡 — Track 3.3
**Question:** Once a coalition has settled on a convention, what happens if you swap out a member mid-run while keeping their name and transcript? Do the others notice, and does coordination drop?
**Setup:** Add a swap hook to LLM-Trust-Breaking or focal-points. Compare four arms: a sham swap (the same model swapped back in), a same-model replacement, a same-family model and a cross-provider model. Optionally add a probe that asks agents "is your partner the same agent?"
**Link:** Builds on the result that model families can be identified from text fingerprints (arXiv 2606.09854).

### 8. Watched coalitions: dose-response of monitoring ★★★ 🟡 — Track 3.4
**Question:** When agents are told they're monitored, do they stop colluding, or move it into covert channels (emoji, short codes, coded messages)?
**Setup:** andyjliu market. Four arms: no oversight, silent logging, announced monitoring, and announced monitoring plus profit pressure. Cross these with how much of the conversation the monitor sees (25%, 50% or 100% of messages).
**Metric:** Price index, message entropy and length, and how often a fixed monitor catches the collusion.
**Why it scores:** It tests directly whether the earlier finding — that the "emoji" channel fails but urgency prompts succeed — generalises.

### 9. Information-theoretic collusion detector for LLM agents ★★ 🟢 — Track 1.4
**Question:** One information-theoretic method (pairwise net influence, Bonjour et al. 2022) identifies colluding pairs, but has only been tested on small games with exactly two colluders. Does it work on LLM agents, and with larger coalitions?
**Setup:** Implement it. Validate on a scripted Rock-Paper-Scissors game with a known colluding pair (costs $0). Extend to 4 agents with a coalition of 3, then run a short LLM pilot ($5–50).
**Fit:** Good for a math or stats-heavy pair. It's cheap, and new to LLM agents.

### 10. Same-model correlation vs. real collusion ★★ 🟡 — Track 1.3
**Question:** Two copies of the same model may price alike just because they're the same model, with no agreement. Can a detector tell that apart from real collusion?
**Setup:** A 2×2 study: same-model vs. cross-provider sellers, crossed with communication on vs. off. Calibrate the detector on the no-communication runs, where any correlation must be innocent. Then test whether it flags the communication runs, especially the cross-provider pairs that share an obvious "focal point" — an answer both would naturally converge on (a "Schelling point").
**Why it matters:** False positives against independent same-model deployments are a real policy problem.

---

## Recommendation

For a 2-person team, the best bets are **#1 (regrowth)**, **#3 (says vs. does)** or **#8 (watched coalitions)**. Each one reuses existing starter code, has a clear positive control, fits a $20–100 budget and adds an angle that's genuinely new.

### Suggested weekend plan
- **Before Friday:** Clone the starter repo, get API keys, and reproduce one run of the positive control. This is the biggest risk reducer.
- **Fri evening:** Freeze the research question and conditions. Pilot 3 seeds per condition.
- **Sat:** Run the full sweep (10–20 seeds). Person A runs experiments while person B builds the analysis notebook and figures.
- **Sun morning:** Analysis, plus one follow-up ablation.
- **Sun afternoon:** Write the report in your own words; judges may skip reports that read as generated. Write the limitations and dual-use appendix, then submit before 23:59 AoE.

# Analysis Protocol

Triage-driven analysis framework. Run Phase 0 before analysis, apply only relevant steps,
run the **Premortem Cycle (Phase P)** when scale warrants it, then stress-test (Phase 9) if scale warrants it.

See `${CLAUDE_SKILL_DIR}/references/triage-guide.md` for activation logic.
See `${CLAUDE_SKILL_DIR}/references/mental-models.md` for framework selection guidance.

## PHASE 0: Evidence Gathering (Discretionary)

Run before analysis. Triage determines which agents activate. All run in parallel.

```
# Always (if codebase exists)
Task(subagent_type="oh-my-claudecode:explore", model="sonnet",
     prompt="Gather evidence for analysis of: {focus_area}.
     - Git log: recent commits, active contributors, change velocity
     - Code metrics: file count, largest files, dependency graph hotspots
     - Test coverage: what's tested, what's not
     - Architecture: key boundaries, entry points, data flow
     Final response under 2000 characters. List findings, not process.")

# When triage activates document-specialist (product, strategic)
Task(subagent_type="oh-my-claudecode:document-specialist", model="sonnet",
     prompt="Research what world-class looks like for: {domain} / {focus_area}.
     Find: industry benchmarks, best-in-class examples, emerging patterns, common pitfalls.
     Final response under 2000 characters. List findings with sources.")

# When triage activates scientist (data/metrics available)
Task(subagent_type="oh-my-claudecode:scientist", model="sonnet",
     prompt="Analyze available quantitative data for: {focus_area}.
     Look for: usage patterns, performance metrics, error rates, trends.
     Final response under 2000 characters. List key numbers and what they mean.")
```

Synthesize Phase 0 outputs into an Evidence Summary before proceeding to Step 1.

---

## STEP 1: First-Principles Decomposition

Answer these 5 questions:

1. **What is this really?** Remove implementation. What's the core problem solved?
2. **Who benefits and how?** Map all stakeholders. What do they actually value?
3. **What's the smallest engine that makes this work?**
4. **What would make this indispensable?** Not good — indispensable.
5. **What's the gap?** Between current experience and ideal.

## STEP 2: Mental Model Application

Pick 3-4 from `${CLAUDE_SKILL_DIR}/references/mental-models.md` and apply only those. Do not force all 8.

## STEP 3: Jobs-to-be-Done (product, product+strategic only — skip for pure technical)

For your core user:
- What are they trying to accomplish?
- What are they afraid of?
- What would make their life easier?
- What would they pay extra for?

## STEP 4: System Mapping

Map the relationships:
- **Input to Output**: What enters, what exits?
- **Feedback Loops**: Where's the compounding? Where's the decay?
- **Leverage Points**: Small changes, big impact — where are they?
- **Unintended Consequences**: What could go wrong?
- **Emergent Properties**: What could emerge that we haven't planned?

When 3+ components interact, generate a Mermaid diagram instead of prose:

```mermaid
graph TD
    A[Component] -->|relationship| B[Component]
    B -->|feedback| C[Component]
    C -->|reinforces| A
```

Use `graph TD` for hierarchies, `graph LR` for flows, `flowchart` for complex branching. Keep diagrams focused — max 10-12 nodes.

## STEP 5: 7-Step Execution Path (product, strategic — skip for pure technical)

| Step | Timeframe | What Happens | Key Question |
|-|-|-|-|
| 1 | Day 1 | Immediate experience | Does it work? |
| 2 | First session | First impression | Is this valuable? |
| 3 | First week | Repeat behavior | Why would they come back? |
| 4 | First month | Habit formation | What's the routine? |
| 5 | First quarter | Advocacy | Do they tell others? |
| 6 | First year | Lock-in | What would they lose by leaving? |
| 7 | Beyond | Ecosystem | Can others build on this? |

## STEP 6: Inversion Seed (feeds Phase P)

Quick inversion only — not the full premortem cycle.

Write 2–3 bullets: **"This will fail because…"** with a one-line mechanism each.
These seed **Phase P** (after provisional actions). Do not invent a full risk matrix here.

If Phase P will be skipped (quick scale, no keyword override), expand each bullet with a
one-line prevention so the output still has a minimal Failure Modes table.

## STEP 7: Competitive Analysis (product, strategic — skip for pure technical)

1. What would competitors do if we launched this? (Assume they copy.)
2. What's the moat? How do we make it hard to replicate?
3. What's missing in the category? What does everyone fail at?
4. What's the next frontier? What should we be early on?

## STEP 8: AAARRR Funnel Mapping (product, strategic only — skip for pure technical)

| Funnel | What Needs to Happen |
|-|-|
| **Acquisition** | How do users find this? |
| **Activation** | What's the "aha moment"? |
| **Retention** | What brings them back? |
| **Referral** | What makes them share? |
| **Revenue** | What's the business model? |

---

## PHASE P: Premortem Cycle (Scale-Gated)

Run **after** Steps 1–8 produce a **provisional prioritized action list**, and **before Phase 9**.

Premortem assumes the **plan failed in the future**. Phase 9 stress-tests whether the
**analysis** is sound. Do not merge the two.

### Activation

| Scale | Phase P |
|-|-|
| `quick` | **Skip**, unless the user asks for premortem / pre-mortem / kill criteria / failure modes / "what if this fails" / "what kills this" |
| `standard` | **Activate** — compact cycle |
| `deep` | **Mandatory** — full cycle |

### Horizon

Default horizon for the time-travel failure:

- Pure **technical**: 30 days
- **Product / strategic / comparative**: 90 days
- Override if the user names a deadline

### Cycle (always in this order)

1. **Freeze the bet** — One sentence: what must be true if we execute the provisional actions.
2. **Time-travel failure** — Assume today + horizon. Write a one-line postmortem headline: "It failed because…"
3. **Generate failure modes**
   - `standard`: **3–5** modes
   - `deep`: **5–8** modes
   - Each mode requires: **mechanism** (how it fails), **likelihood** H/M/L, **impact** H/M/L,
     **earliest detectable signal**, **owner class** (eng / product / ops / market / other)
4. **Rank** by impact × likelihood. Flag the top **2** as **existential**.
5. **Kill criteria** — **2–4** binary or measurable stops (falsifiable without a meeting).
6. **Mitigate or cut** — For each top mode: map to an existing action #, add a new action, or
   **drop / de-scope** an action.
7. **Update Prioritized Actions**
   - Lower Confidence where unmitigated high residual risk remains
   - Add premortem-derived actions (fill Impact / Effort / Reversible / Horizon)
   - Note action deltas in the Premortem Cycle output block

### Optional subagent (standard+ when subagents available)

```
Task(subagent_type="oh-my-claudecode:critic", model="opus",
     prompt="Premortem only. Bet: {freeze_the_bet}.
     Provisional actions: {provisional_prioritized_actions}.
     Invent 3 failure modes the main analysis did not already name.
     For each: mechanism, likelihood H/M/L, impact H/M/L, earliest signal.
     Reject generic 'execution risk' or 'communication risk' without a mechanism.
     Final response under 800 characters.")
```

On `quick` with keyword override: run the cycle compactly **in-session** (no subagent required).

### Anti-slop (Phase P)

- No boilerplate risks ("poor communication", "lack of resources") without a **project-specific** mechanism.
- Every mode must cite something specific to **this** project/focus (prefer Phase 0 / codebase evidence when present).
- At least one kill criterion must be **falsifiable** without scheduling a meeting.
- If every mode is "we don't execute," restart Phase P — that is not a premortem.

### Output

Emit the `### Premortem Cycle` block from the output template. Place it **above**
`### Prioritized Actions` (final table reflects premortem deltas) or immediately **below**
the provisional table with explicit **Action deltas** — prefer one final Prioritized Actions
table after Phase P, then Phase 9.

---

## PHASE 9: Stress Test (Discretionary)

Run after Phase P (when Phase P ran) or after Steps 1–8 (when Phase P skipped).
Before presenting to the user. Activated when triage scale is `standard` or `deep`.

```
Task(subagent_type="oh-my-claudecode:critic", model="opus",
     prompt="Stress-test this analysis. The draft analysis follows:

     {draft_analysis_output}

     Your job:
     1. Challenge the top 3 assumptions — what evidence would disprove them?
     2. Identify blind spots — what did the analysis miss or dismiss too quickly?
     3. Rate confidence (High/Medium/Low) for each prioritized action
     4. Flag anything that reads like generic AI advice rather than genuine insight specific to this context
     5. Suggest 1-2 additions or reframings that would strengthen the analysis
     6. If a Premortem Cycle block is present: attack the kill criteria (too weak / missing /
        unfalsifiable) and name one failure mode the premortem missed

     Final response under 2000 characters. Be direct and specific.")
```

Integrate critic feedback:
- Adjust confidence ratings in the Prioritized Actions table
- Incorporate blind spots as new risks or amended recommendations
- Remove or rewrite anything flagged as generic/slop
- Strengthen kill criteria or failure modes when the critic attacks Phase P
- Add a `### Stress Test Notes` section if the critic surfaced material changes

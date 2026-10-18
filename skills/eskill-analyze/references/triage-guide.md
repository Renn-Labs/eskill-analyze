# Router (Triage)

Decide the least engine work that still gives a world-class answer. Work in three waves, after Atom of Thoughts: answer the independent atoms first, then contract what is left into a smaller, self-contained question. Print the Route line before spending on agents or models.

## Step 0: Atomize — Wave 1 (in-session, seconds)

| Atom | Question |
|-|-|
| a1 Outcome | What is the ask really for? |
| a2 Sufficiency | Can it be answered well from what is already in context? |
| a3 Premise | Does the ask carry a premise that may be false, or a digested proxy (a dashboard number, a summary) for the real question? |
| a4 Options | Is there a real choice between meaningfully different options? |

Also answer the four deepening questions, internally (after Felix Rieseberg, "How to be more ambitious: A tutorial for humans with models", 2026-10-13): what a top practitioner would do here that wasn't asked; the rawest material they would start from; the field's instruments they would use; what, other than the model or the user, would show the result is right. Phrase each as an action, never a persona. They feed later atoms and surface where they belong — rawest material in Evidence, instruments in the analysis, the verifier in the Verifier column, the expert move as an action or a reframe — never as a block of their own, except as the output of `/esa deepen`.

If the answers change the ask, restate it in one line (`**Ask, deepened**:`). Proceed unless that changes scope materially — a different project or primary stakeholder, or work needing access, data, budget, or time the user has not granted; then ask one question offering both asks. Go one layer down; never add workstreams.

**Contract:** "Given outcome a1, sufficiency a2, premise risk a3 and options a4, which modules run?" Waves and contracts stay internal; the reader sees the Route line and results.

## Wave 2: Select Modules

| Atom | Question | Module if yes |
|-|-|-|
| a5 Evidence | Is evidence missing that a raw source could supply? | Phase 0 Evidence, raw first (on `quick`: one raw read in-session, no agents) |
| a6 Irreversibility | Is there a decision that is expensive to undo? | Phase P Premortem |
| a7 Other fields | Would another field's instrument change the answer? | Borrow (Range) |
| a8 Follow-on work | Will work follow from the answer? | Actions + Verifier; Project impact when project context exists |

Lenses generate atoms; they are not labels. **Depth** raises a5 and the Instruments rule when the answer turns on data, code, or instruments below the task's layer. **Range** raises a7 when the deliverable's verbs belong to other fields. **Altitude** turns a1 into a reframe when the ask is a task serving an unstated outcome (weak for creative work). Speed is the default.

Run core-analysis steps (Steps 1-8) only where they answer an atom: Step 1 for a1 or a3; Step 2 whenever any analysis runs; Step 4 when 3+ parts interact; Steps 3, 5, 7, 8 for product or strategic asks only; Step 6 whenever Actions run (the seed for Phase P, or the thin risk table without it). Phase P needs a provisional action list, so it brings Actions and the steps that produce them.

If a2 is yes and a3, a4, a6 are no, run no modules: answer inline with a Verifier line (security signals still get the reviewer; see Invariants).

**Contract:** "Given the modules chosen and what is at stake, how much independent checking does this need?"

## Wave 3: Choose the Check (a9)

| Stakes | Phase 9 |
|-|-|
| Inline answer, or reversible and low stakes | None |
| A plan others will act on | Critic |
| Irreversible; money-, security- or reputation-adjacent; "world-class" language | Critic, mandatory |

Higher tiers (`esat`, `esat-fleet`, `esat-frontier`) are an explicit request for their panel: a9 is decided, and their panel replaces the critic.

## Type and Scale

Type picks models and agents; scale sets module depth.

| Type | Signals |
|-|-|
| `technical` | codebase, architecture, performance, API, infra, DX, tests, CI/CD, latency |
| `product` | users, retention, growth, onboarding, UX, conversion, pricing |
| `strategic` | roadmap, competitive, positioning, market, moat, invest, pivot |
| `comparative` | side-by-side evaluation of meaningfully different approaches; implicit build-vs-buy ("we built X, but vendor Y just launched Z") |

Not comparative: an "X or Y" that is really a technical decision; one option being "do nothing" (add Reversibility instead); "compared to what McKinsey would produce" (that is the world-class definition). Ties: strategic > product > technical. `comparative` combines with any type.

| Scale | Signals | Phase P | Phase 9 |
|-|-|-|-|
| `quick` | One focused question, "just tell me" | Compact, only when a6 or keywords | No |
| `standard` | A feature, system, or product area | Compact (3–5 modes) when a6 | When a9 says so |
| `deep` | Multi-system, high-stakes, "world-class" | Full (5–8 modes), mandatory | Mandatory |

Premortem keywords activate Phase P at any scale: premortem, pre-mortem, kill criteria, failure modes, "what if this fails", "what kills this", or an explicit stop/abort plan. Bump `quick` → `standard` when the answer needs codebase evidence; "world-class" language means `deep`.

## Agents by Module

| Module | Agents |
|-|-|
| Phase 0 Evidence | explore (codebase), document-specialist (primary sources), scientist (raw data), security-reviewer (auth, tokens, secrets, PII, payments, trading) |
| Core analysis | analyst; architect for technical or strategic systems |
| Compare | per option: explore + architect + analyst if it exists, document-specialist + analyst if hypothetical |
| Phase P, Phase 9 | critic |

Spawn only what the running modules name; skip explore when no codebase is relevant.

## Invariants (never skipped)

- Every action that exists has an outside Verifier, or `none — unverifiable` with Confidence L.
- Cited evidence carries a `raw` or `digested` tag.
- Irreversible decisions get Phase P, at any scale.
- Security signals (auth, tokens, secrets, permissions, PII, payments, trading) get security-reviewer, even inline.
- At `deep`, the checker is not the maker.

**Escalate up:** when an atom's answer raises the stakes (an irreversible migration, money at risk), add the module and say so in one line. **Contradiction rule:** when evidence contradicts a route the user chose, say so and let them redirect; never override silently. **Stop:** after each wave, restate what remains in one internal sentence and drop resolved detail; stop when it is atomic or at budget, and name what stayed open.

## Output

```
**Route**: {type}/{scale} · modules: {those that ran, or none} · models: {3-4, or none}
**Ask, deepened**: {one line, only if Step 0 changed the ask}
```

At most 20 words, no reasons: a skipped module is simply absent.

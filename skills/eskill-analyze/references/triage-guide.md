# Triage Guide

Classify every analysis prompt before executing. This determines which phases, agents, and mental models activate.

## Step 1: Classify Type

| Type | Trigger Keywords / Signals | Example |
|-|-|-|
| `technical` | codebase, architecture, refactor, performance, API, database, infra, DX, tests, CI/CD, pipeline, latency | "Analyze our auth middleware" |
| `product` | users, retention, growth, onboarding, UX, conversion, pricing, feature | "How do we improve onboarding?" |
| `strategic` | roadmap, competitive, positioning, market, long-term, vision, pivot, moat, invest, next quarter | "Where should we invest next quarter?" |
| `comparative` | "vs", "compare", "which is better", "trade-offs between", "A or B", implicit build-vs-buy* | "Monorepo vs polyrepo for our team" |

\* **Implicit comparison detection:** Patterns like "we built X but [vendor/alternative] just launched/released/offers Y" signal a build-vs-buy decision even without explicit comparison language. Classify as `comparative` + the relevant secondary type.

**Comparative false-positive filter:**
- "or" alone is not enough — "should we use X or Y" is often a technical decision question, not a full comparison. Only classify as `comparative` when the prompt asks for side-by-side evaluation of meaningfully different approaches.
- If one option is clearly "do nothing / keep current," treat as the non-comparative type with Reversibility model added.
- **Benchmark vs choice:** "How does X compare to [abstract standard]" (e.g., "compared to what McKinsey would produce") is NOT a comparison — it's a standard analysis where the abstract standard becomes the World-Class Definition input. Route as the non-comparative type.

If multiple types match, use the dominant one. When types are equally weighted, use this priority: **strategic > product > technical** (higher-level framing produces more actionable output; technical constraints surface as dependencies within the analysis). `comparative` can combine with any other type.

## Step 2: Classify Scale

| Scale | Signals | Stress Test? |
|-|-|-|
| `quick` | Single focused question, narrow scope, "just tell me" | No |
| `standard` | Feature, system, or product area analysis | Yes |
| `deep` | Strategic, high-stakes, multi-system, "world-class" language | Yes (always) |

**Override rules:**
- Bump `quick` → `standard` if the question requires codebase evidence to answer (e.g., "what's wrong with our test coverage?" is narrow but needs data).
- "world-class" language always triggers `deep`, regardless of scope.

## Step 3: Select Agents

| Agent | Always | Technical | Product | Strategic | Comparative |
|-|-|-|-|-|-|
| analyst (opus) | Yes | Yes | Yes | Yes | Yes (per option) |
| architect (opus) | - | Yes | - | Yes | Yes (per option) |
| explore (sonnet) | Yes* | Yes | If codebase exists | Yes | Per option (skip for hypothetical options**) |
| document-specialist (sonnet) | - | If deep scale or "world-class" | Yes | Yes | Yes (for framework/tool comparisons); otherwise if external context needed |
| scientist (sonnet) | - | If metrics/data implied*** | If data available | If data available | If data/metrics implied*** |
| security-reviewer (sonnet) | - | If security keywords**** | - | - | If security-relevant |
| critic (opus) | - | If standard+ | If standard+ | Always | Always |

\* Skip explore if no codebase is relevant (pure strategy/market analysis).
\** For asymmetric comparisons (one option exists in codebase, one is hypothetical): run explore only for the existing option. For the hypothetical option, activate document-specialist instead.
\*** Default to activating scientist if the domain strongly implies data exists (usage patterns, error rates, latency, metrics, logs, financial data). Explore output can deactivate if no evidence found.
\**** Security keywords: auth, permissions, tokens, secrets, encryption, RBAC, CORS, injection, XSS, OWASP, trading, financial, order, payment, PII, HIPAA.

**Comparative ceiling:** Cap at 2 options. For 3+ options, shortlist to 2 finalists first using a quick-triage pass before running full analysis.

## Step 4: Select Mental Models

| Analysis Type | Recommended Models |
|-|-|
| Technical / codebase | First Principles + Coupling/Cohesion + Complexity Budget + Scalability Ceiling |
| Technical / performance | Scalability Ceiling + First Principles + Feedback Loops + Complexity Budget |
| Technical / DX | DX Friction Mapping + First Principles + Feedback Loops |
| Technical / security | Security Surface + Inversion + Coupling/Cohesion |
| Technical / data-observability | First Principles + Feedback Loops + Scalability Ceiling + DX Friction Mapping |
| Product / growth | JTBD + Unit Economics + 7-Step Ahead + AAARRR |
| Product / UX | JTBD + Four Levels + Feedback Loops |
| Strategic / positioning | Inversion + Feedback Loops + Unit Economics + Reversibility |
| Comparative | First Principles + Inversion + Reversibility (applied to each option) |

Pick 3-4 max from the recommended set. Never force all models.

**Sub-type overlap:** When a prompt spans two sub-types within the same type (e.g., onboarding = UX + growth), merge the recommended sets and pick 4 from the union.

**Cross-type dependency:** When the primary type has a strong secondary constraint from another type (e.g., strategic decision with gnarly technical integration, or product feature with security implications), add 1 model from the secondary type's set. E.g., strategic + technical risk → add Complexity Budget or Coupling/Cohesion to the strategic set.

## Step 5: Select Phases

| Phase | Quick | Standard | Deep |
|-|-|-|-|
| Phase 0: Evidence Gathering | Skip | Activate relevant agents | Activate all applicable agents |
| Steps 1-8: Analysis Protocol | Pick 3-4 relevant steps | Pick 4-6 relevant steps | All applicable steps with selected frameworks* |
| Phase 9: Stress Test | Skip | Run critic | Run critic (mandatory) |

\* Skip steps clearly irrelevant to the analysis type. E.g., AAARRR (Step 8) and Competitive Analysis (Step 7) are product/strategic only — skip for pure technical analyses. JTBD (Step 3) is product only — skip for pure engineering questions.

## Output

State your triage result at the start of every analysis:

```
**Triage**: {type} / {scale}
**Agents**: {list of activated agents}
**Models**: {list of selected mental models}
**Phases**: {which phases are active}
```
